"""TokenScope loopback HTTP application."""
import argparse
import csv
import io
import json
import socket
import threading
import webbrowser
import urllib.request
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import cloud, logs, store
from .login import LoginFlow

WEB = Path(__file__).resolve().parents[1] / "web"
LOCK=threading.Lock()
STOP=threading.Event()
LOGIN=LoginFlow()


class LocalServer(ThreadingHTTPServer):
    # Double-clicking again must reopen the same dashboard and login flow.
    def server_bind(self):
        if hasattr(socket,"SO_EXCLUSIVEADDRUSE"):
            self.allow_reuse_address=False
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        super().server_bind()


def run_sync(only=None):
    try:
        with closing(store.connect()) as db:
            for p in db.execute("SELECT * FROM profiles WHERE enabled=1 ORDER BY id").fetchall():
                if STOP.is_set() or only is not None and p["id"]!=only:
                    continue
                if p["cloud"]:
                    with db:
                        db.execute("UPDATE profiles SET cloud_attempt=?,cloud_client=NULL WHERE id=?",(store.now(),p["id"]))
                    try:
                        cloud.collect(db,p)
                    except Exception as e:
                        status=cloud.diagnostic("云端采集",e)
                        action="login" if isinstance(e,cloud.LoginRequired) else "install" if isinstance(e,cloud.MissingClient) else ""
                        with db:
                            db.execute("UPDATE profiles SET cloud_status=?,auth_action=? WHERE id=?",(status,action,p["id"]))
                        if action=="login" or any(x in status for x in ("身份","账号已切换","已关联其他","其他登录方式")):
                            continue
                if p["logs"]:
                    try:
                        logs.collect(db,db.execute("SELECT * FROM profiles WHERE id=?",(p["id"],)).fetchone())
                    except Exception:
                        with db:
                            db.execute("UPDATE profiles SET log_status='日志读取失败，请检查目录及权限' WHERE id=?",(p["id"],))
    finally:
        LOCK.release()


def trigger(only=None):
    if not LOCK.acquire(False):
        return False
    threading.Thread(target=run_sync,args=(only,),daemon=True).start()
    return True


def sync_after_login(profile_id):
    LOCK.acquire()
    run_sync(profile_id)
    with closing(store.connect()) as db:
        row=db.execute("SELECT enabled,cloud_status FROM profiles WHERE id=?",(profile_id,)).fetchone()
    return "登录已完成。"+(row["cloud_status"] if row and row["enabled"] else "此账号已暂停采集。")


def periodic():
    while not STOP.is_set():
        trigger()
        STOP.wait(900)


def profiles(db):
    result=[]
    for r in db.execute("SELECT * FROM profiles ORDER BY id"):
        p=dict(r)
        p.pop("binding")
        p["summary"]=json.loads(p["summary"] or "{}")
        p["summary"].pop("workspace_digest",None)
        p["rates"]=json.loads(p["rates"] or "{}")
        if p["cloud"]:
            extent=db.execute("SELECT COUNT(*),MIN(day),MAX(day) FROM days WHERE profile=?",(p["id"],)).fetchone()
            p["days_saved"],p["first_day"],p["last_day"]=extent
        result.append(p)
    return {"profiles":result,"busy":LOCK.locked(),"login":LOGIN.snapshot()}


def profile_add(db,data):
    name=store.label(data.get("name"),"账号名称",50)
    tool=data.get("tool")
    if tool not in logs.ADAPTERS:
        raise ValueError("未知工具")
    root=Path(store.label(data.get("root"),"配置目录",1024)).expanduser()
    if not root.is_absolute() or not root.is_dir():
        raise ValueError("请选择本机已有目录的绝对路径")
    cloud_on=int(tool=="Codex" and data.get("cloud") is True)
    logs_on=int(data.get("logs") is True)
    if not cloud_on and not logs_on:
        raise ValueError("请选择采集来源")
    with db:
        db.execute("INSERT INTO profiles(name,tool,root,cloud,logs) VALUES(?,?,?,?,?)",
                   (name,tool,str(root.resolve()),cloud_on,logs_on))


class Handler(BaseHTTPRequestHandler):
    server_version="TokenScope"
    def log_message(self,*args):
        pass

    def respond(self,body,typ="application/json; charset=utf-8",status=200,filename=None):
        if not isinstance(body,bytes):
            body=json.dumps(body,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type",typ)
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if filename:
            self.send_header("Content-Disposition",f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def route(self,post):
        host=f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host")!=host:
            return self.respond({"error":"无效的本机地址"},status=403)
        url=urlsplit(self.path)
        q={k:v[-1] for k,v in parse_qs(url.query).items()}
        if post:
            origin=self.headers.get("Origin")
            request_marker = self.headers.get("X-TokenScope-Request", self.headers.get("X-Atlas-Request"))
            if (origin and origin!="http://"+host) or request_marker!="1" or self.headers.get_content_type()!="application/json":
                return self.respond({"error":"请求来源无效"},status=403)
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=20*1024*1024:
                return self.respond({"error":"请求正文为空或超过 20 MiB"},status=413)
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):
                raise ValueError("请求必须为对象")
        elif url.path in ("/","/app.css","/app.js","/language.js","/messages.js"):
            f=WEB/({"/":"index.html"}.get(url.path,url.path[1:]))
            typ={".js":"text/javascript",".css":"text/css",".html":"text/html"}[f.suffix]
            return self.respond(f.read_bytes(),typ+"; charset=utf-8")
        with closing(store.connect()) as db:
            if not post and url.path=="/api/status":
                return self.respond(profiles(db))
            if not post and url.path=="/api/report":
                return self.respond(store.query(db,q))
            if not post and url.path=="/api/export":
                rows=store.query(db,q,True)
                if q.get("format")=="csv":
                    fields=("day","account","tool","total_tokens","source") if q.get("view","cloud")=="cloud" else (*store.FIELDS,"source")
                    out=io.StringIO(newline="")
                    writer=csv.DictWriter(out,fieldnames=fields)
                    writer.writeheader()
                    for r in rows:
                        writer.writerow({k:"'"+v if isinstance(v,str) and v.startswith(("=","+","-","@")) else v for k,v in r.items()})
                    return self.respond(out.getvalue().encode("utf-8-sig"),"text/csv; charset=utf-8",filename="tokenscope.csv")
                return self.respond(rows,filename="tokenscope.json")
            if post and url.path=="/api/import":
                if not isinstance(data.get("content"),str):
                    raise ValueError("导入内容无效")
                return self.respond(store.ingest(db,data.get("format"),data["content"]))
            if post and url.path=="/api/profile":
                profile_add(db,data)
                return self.respond({"ok":True})
            if post and url.path=="/api/toggle":
                with db:
                    if not db.execute("UPDATE profiles SET enabled=1-enabled WHERE id=?",(int(data["id"]),)).rowcount:
                        raise ValueError("账号不存在")
                return self.respond({"ok":True})
            if post and url.path=="/api/sync":
                return self.respond({"started":trigger()})
            if post and url.path=="/api/login":
                profile=db.execute("SELECT * FROM profiles WHERE id=?",(int(data["id"]),)).fetchone()
                if not profile:
                    raise ValueError("账号不存在")
                return self.respond(LOGIN.start(profile,sync_after_login))
            if post and url.path=="/api/login/cancel":
                return self.respond({"cancelled":LOGIN.cancel(data["ticket"])})
            if post and url.path=="/api/stop":
                STOP.set()
                threading.Thread(target=self.server.shutdown,daemon=True).start()
                return self.respond({"ok":True})
        self.respond({"error":"未找到"},status=404)

    def handle_route(self,post):
        try:
            self.route(post)
        except store.sqlite3.IntegrityError:
            self.respond({"error":"账号名称或配置目录已存在"},status=400)
        except (ValueError,TypeError,KeyError,csv.Error):
            import sys
            err=sys.exc_info()[1]
            message=str(err) if type(err) is ValueError else "内容或字段格式不正确"
            self.respond({"error":message},status=400)
        except (BrokenPipeError,ConnectionResetError):
            pass
        except Exception:
            self.respond({"error":"处理失败，请检查磁盘空间或数据库状态"},status=500)

    def do_GET(self):
        self.handle_route(False)

    def do_POST(self):
        self.handle_route(True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--no-browser",action="store_true")
    parser.add_argument("--manual",action="store_true",help="disable scheduled sync")
    args=parser.parse_args()
    store.setup()
    try:
        listener=LocalServer(("127.0.0.1",args.port),Handler)
    except OSError:
        url=f"http://127.0.0.1:{args.port}/"
        with urllib.request.urlopen(url+"api/status",timeout=3) as res:
            if not res.headers.get("Server","").startswith("TokenScope ") or "profiles" not in json.load(res):
                raise RuntimeError("端口已被占用，请用 --port 指定其他端口")
        print("TokenScope is already running: "+url,flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        return
    with listener as server:
        url=f"http://127.0.0.1:{server.server_port}/"
        print(f"TokenScope  {url}   (Ctrl+C to stop)",flush=True)
        if not args.manual:
            threading.Thread(target=periodic,daemon=True).start()
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            STOP.set()
            LOGIN.cancel(LOGIN.snapshot().get("ticket"))
            LOGIN.finished.wait(35)
            # A read-only client and any SQLite transactions finish before shutdown.
            with LOCK:
                pass

if __name__=="__main__":
    main()
