import csv
import io
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer

from tools import app, cloud, logs, store


def event(**values):
    return dict(dict(event_id="evt-1",account="A",tool="Other",model="unit",timestamp="2026-02-01T12:00:00Z",
                input_tokens=100,output_tokens=25,cached_tokens=60,cache_write_tokens=3),**values)


def as_csv(rows):
    f=io.StringIO(newline="")
    writer=csv.DictWriter(f,fieldnames=store.FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return f.getvalue()


class DatabaseLocation(unittest.TestCase):
    def test_default_location_and_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "LOCALAPPDATA": tmp, "TOKENSCOPE_DATA": "", "TOKEN_ATLAS_DATA": ""
        }):
            current = Path(tmp) / "TokenScope" / "tokenscope.sqlite3"
            previous = Path(tmp) / "TokenAtlas" / "atlas.sqlite3"
            self.assertEqual(store.database_path(), current)
            with patch.object(store, "DATABASE", previous):
                store.setup()
                with closing(store.connect()) as db, db:
                    store.ingest(db, "json", json.dumps([event()]))
            self.assertEqual(store.database_path(), previous)
            with patch.object(store, "DATABASE", store.database_path()):
                store.setup()
                with closing(store.connect()) as db:
                    self.assertEqual(db.execute("SELECT event_id FROM events").fetchone()[0], "evt-1")
            self.assertFalse(current.exists())
            current.parent.mkdir()
            current.touch()
            self.assertEqual(store.database_path(), current)

    def test_custom_data_directory(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "TOKENSCOPE_DATA": "", "TOKEN_ATLAS_DATA": tmp
        }):
            previous = Path(tmp) / "atlas.sqlite3"
            previous.touch()
            self.assertEqual(store.database_path(), previous)
            directory = Path(tmp) / "custom"
            with patch.dict(os.environ, {"TOKENSCOPE_DATA": str(directory)}):
                self.assertEqual(store.database_path(), directory / "tokenscope.sqlite3")


class Ledger(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.data=patch.object(store,"DATABASE",self.root/"db"/"tokenscope.sqlite3")
        self.data.start()
        self.addCleanup(self.data.stop)
        store.setup()
        self.db=store.connect()
        self.addCleanup(self.db.close)
        self.profile=self.db.execute("SELECT * FROM profiles WHERE tool='Codex'").fetchone()

    def report(self,**q):
        return store.query(self.db,dict({"view":"detail","range":"all"},**q))

    def import_rows(self,*rows):
        return store.ingest(self.db,"json",json.dumps(rows))

    def test_cross_format_is_idempotent(self):
        self.assertEqual(self.import_rows(event())["added"],1)
        self.assertEqual(store.ingest(self.db,"csv","\ufeff"+as_csv([event()]))["added"],0)
        r=self.report()
        self.assertEqual(r["total"],125)
        self.assertEqual(r["parts"]["cached_tokens"],60)

    def test_conflicting_batch_rolls_back(self):
        self.import_rows(event())
        with self.assertRaises(ValueError):
            self.import_rows(event(event_id="evt-2"),event(output_tokens=26))
        self.assertEqual(self.report()["total"],125)

    def test_strict_fields(self):
        for bad in [dict(cached_tokens=110),dict(output_tokens=True),dict(input_tokens=-1),
                    dict(input_tokens=4.5),dict(timestamp="2026-01-01"),dict(model="")]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                self.import_rows(event(**bad))

    def test_ranges_filters_and_export(self):
        self.import_rows(event(),event(account="B",tool="Claude Code",model="mini",timestamp="2026-02-03T12:00:00Z"))
        r=self.report(range="custom",start="2026-02-01",end="2026-02-04")
        self.assertEqual((r["active"],r["peak"],r["span"],r["average"]),(2,125,4,62.5))
        self.assertEqual(self.report(account="B",tool="Claude Code",model="mini")["total"],125)
        self.assertEqual(self.report(account="B",model="unit")["total"],0)
        rows=store.query(self.db,{"view":"detail","range":"all","account":"A"},True)
        self.assertEqual(len(rows),1)
        self.assertEqual(self.import_rows(*rows)["added"],0)
        self.assertIsNone(self.report(view="cloud")["total"])
        with self.assertRaises(ValueError):
            self.report(range="custom",start="2026-02-04",end="2026-02-01")

    def test_timezone_normalization(self):
        a=store.normalize(event(timestamp="2026-02-02T00:30:00+08:00"))
        b=store.normalize(event(timestamp="2026-02-01T16:30:00Z"))
        self.assertEqual(a,b)

    def test_codex_append_partial_replay_and_model(self):
        f=self.root/"rollout.jsonl"
        def record(i,o,c):
            return json.dumps(dict(timestamp="2026-02-01T10:00:00Z",type="event_msg",payload=dict(type="token_count",
                info=dict(total_token_usage=dict(input_tokens=i,output_tokens=o,cached_input_tokens=c)))))+"\n"
        prefix='{"type":"session_meta","payload":{"id":"session"}}\n{"type":"turn_context","payload":{"model":"gpt-example"}}\n'
        f.write_bytes((prefix+record(100,30,40)+record(100,30,40)+record(140,35,50)[:-1]).encode())
        self.assertEqual(logs.scan_file(self.db,self.profile,f,logs.codex,None),(1,0))
        with f.open("ab") as stream:stream.write(b"\n")
        self.assertEqual(logs.scan_file(self.db,self.profile,f,logs.codex,None),(1,0))
        self.assertEqual(logs.scan_file(self.db,self.profile,f,logs.codex,None),(0,0))
        r=self.report()
        self.assertEqual((r["total"],r["parts"]["cached_tokens"],r["dims"]["model"]),(175,50,["gpt-example"]))
        f.write_text(prefix+record(100,30,40),encoding="utf8")
        self.assertEqual(logs.scan_file(self.db,self.profile,f,logs.codex,None),(0,0))

    def test_claude_stream_and_cache_accounting(self):
        profile=dict(self.profile,tool="Claude Code")
        p=self.root/"messages.jsonl"
        rows=[]
        for n in [0,20,20,0]:
            rows.append(dict(type="assistant",timestamp="2026-02-01T10:00:00Z",requestId="r",
                             message=dict(id="m",model="sonnet-example",usage=dict(input_tokens=10,output_tokens=n,
                             cache_read_input_tokens=40,cache_creation_input_tokens=30))))
        p.write_text("bad line\n"+"".join(json.dumps(x)+"\n" for x in rows),encoding="utf8")
        self.assertEqual(logs.scan_file(self.db,profile,p,logs.claude,None),(1,1))
        self.assertEqual(self.report()["total"],100)
        self.assertEqual(self.report()["parts"]["cache_write_tokens"],30)

    def test_cloud_upsert_and_identity(self):
        class Client:
            owner="account-a"
            tokens=45
            def __init__(self,home,secure=False,exe=None):pass
            def send(self,msg):pass
            def close(self):pass
            def call(self,method,params):
                if method=="account/read":
                    return {"account":{"type":"chatgpt","email":"anon@example.test"},"workspaceRouting":{"chatgptAccountId":self.owner}}
                if method=="account/usage/read":
                    return {"summary":{"lifetimeTokens":1000},"dailyUsageBuckets":[{"startDate":"2026-02-01","tokens":self.tokens}]}
                if method=="account/rateLimits/read":
                    raise cloud.Unavailable("test unavailable")
                return {}
        def collect():
            cloud.collect(self.db,self.db.execute("SELECT * FROM profiles WHERE id=?",(self.profile["id"],)).fetchone())
        with patch.object(cloud,"Client",Client), patch.object(cloud,"candidates",return_value=["test-codex"]):
            collect()
            Client.tokens=55
            collect()
            self.assertEqual(self.report(view="cloud")["total"],55)
            Client.owner="account-b"
            with self.assertRaises(cloud.Unavailable):collect()
            self.assertEqual(self.report(view="cloud")["total"],55)
            self.assertIsNone(self.report(view="cloud")["parts"])

    def test_import_examples(self):
        sample=Path(__file__).resolve().parents[1]/"examples"
        a=store.ingest(self.db,"json",(sample/"usage.json").read_text(encoding="utf8"))
        b=store.ingest(self.db,"csv",(sample/"usage.csv").read_text(encoding="utf-8-sig"))
        self.assertGreater(a["added"],0)
        self.assertEqual((a["added"],0),(b["read"],b["added"]))

    def test_optional_daily_buckets(self):
        rows,summary=cloud.daily_rows({"dailyUsageBuckets":None,"summary":{"lifetimeTokens":400,"peakDailyTokens":None}})
        self.assertEqual(rows,[])
        self.assertEqual(summary,{"lifetimeTokens":400})

    def test_cloud_missing_and_real_zero(self):
        blank=self.report(view="cloud")
        self.assertEqual([blank[k] for k in ("total","average","peak","active")],[None]*4)
        self.assertIn(self.profile["name"],blank["dims"]["account"])
        self.db.execute("INSERT INTO days VALUES(?,?,?)",(self.profile["id"],"2026-02-01",0))
        self.db.commit()
        zero=self.report(view="cloud")
        self.assertEqual((zero["total"],zero["active"],zero["reported"]),(0,0,1))
        self.assertIsNone(self.report(view="cloud",range="custom",start="2026-02-02",end="2026-02-03")["total"])

    def test_cloud_uses_compatible_client(self):
        attempted=[]
        class Stub:
            def __init__(self,home,secure=False,exe=None):
                self.exe=exe
                attempted.append(exe)
            def send(self,msg):pass
            def close(self):pass
            def call(self,method,params):
                if method=="account/read":
                    return {"account":{"type":"chatgpt","email":"test@example.test"}}
                if method=="account/usage/read":
                    if self.exe=="old":
                        raise cloud.rpc_error(method,{"code":-32601})
                    return {"summary":{"lifetimeTokens":500},"dailyUsageBuckets":[{"startDate":"2026-02-01T00:00:00Z","tokens":123}]}
                return {}
        with patch.object(cloud,"Client",Stub), patch.object(cloud,"candidates",return_value=["old","desktop"]):
            cloud.collect(self.db,self.profile)
        self.assertEqual(attempted,["old","desktop"])
        self.assertEqual(self.report(view="cloud")["total"],123)
        state=app.profiles(self.db)["profiles"][0]
        self.assertTrue(state["cloud_client"].endswith("desktop"))
        self.assertEqual(state["account_hint"],"t***@example.test")

    def test_cloud_errors_are_actionable_and_redacted(self):
        denied=cloud.rpc_error("account/usage/read",{"code":-32603,"message":"HTTP 403 secret-example"})
        self.assertIn("403",str(denied))
        self.assertNotIn("secret-example",str(denied))
        denied=PermissionError()
        denied.winerror=5
        self.assertIn("WinError 5",cloud.diagnostic("启动 Codex 客户端",denied))
        with self.assertRaises(cloud.Unavailable):
            cloud.daily_rows({"summary":{},"dailyUsageBuckets":[{"startDate":"invalid","tokens":0}]})

    def test_codex_account_mismatch(self):
        path=self.root/"mixed.jsonl"
        meta={"type":"session_meta","payload":{"id":"session","creator_account_id":"other"}}
        usage={"type":"event_msg","timestamp":"2026-02-01T10:00:00Z","payload":{"type":"token_count",
               "info":{"last_token_usage":{"input_tokens":30,"output_tokens":10}}}}
        path.write_text(json.dumps(meta)+"\n"+json.dumps(usage)+"\n",encoding="utf8")
        self.assertEqual(logs.scan_file(self.db,self.profile,path,logs.codex,store.digest("expected")),(0,0))
        self.assertEqual(self.report()["total"],0)

    def test_http_entry_points(self):
        server=ThreadingHTTPServer(("127.0.0.1",0),app.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url=f"http://127.0.0.1:{server.server_port}"
        def read(path,**kw):
            with urllib.request.urlopen(urllib.request.Request(url+path,**kw),timeout=5) as res:
                return res.read()
        self.assertIn(b"TokenScope",read("/"))
        for path in ["/app.js","/app.css","/api/status","/api/report"]:self.assertTrue(read(path))
        headers={"Content-Type":"application/json","X-TokenScope-Request":"1"}
        data=json.dumps({"format":"json","content":json.dumps([event()])}).encode()
        with self.assertRaises(urllib.error.HTTPError) as denied:
            read("/api/import",data=data,headers={**headers,"Origin":"https://outside.test"})
        self.assertEqual(denied.exception.code,403)
        self.assertEqual(json.loads(read("/api/import",data=data,headers=headers))["added"],1)
        rows=list(csv.DictReader(io.StringIO(read("/api/export?view=detail&range=all&format=csv").decode("utf-8-sig"))))
        self.assertEqual(rows[0]["event_id"],"evt-1")
        self.assertEqual(json.loads(read("/api/export?view=cloud&range=all")),[])
        add={"name":"work","tool":"Codex","root":str(self.root),"cloud":True,"logs":True}
        read("/api/profile",data=json.dumps(add).encode(),headers=headers)
        records=json.loads(read("/api/status"))["profiles"]
        self.assertEqual(len(records),3)
        read("/api/toggle",data=json.dumps({"id":records[-1]["id"]}).encode(),headers=headers)
        self.assertEqual(json.loads(read("/api/status"))["profiles"][-1]["enabled"],0)

