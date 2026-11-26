import queue
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from tools import cloud, login, store


class FakeClient:
    def __init__(self):
        self.completions=queue.Queue()
        self.logged=False
        self.closed=False
        self.calls=[]

    def call(self,method,params):
        self.calls.append(method)
        if method=="account/login/start":
            return {"loginId":"this-flow","authUrl":"https://auth.openai.com/oauth/authorize?state=test"}
        if method=="account/login/cancel":
            return {"status":"canceled"}
        if method=="account/read":
            return {"account":{"email":"test@example.test","type":"chatgpt"} if self.logged else None}
        raise AssertionError(method)

    def close(self):
        self.closed=True


class LoginTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p=patch.object(store,"DATABASE",Path(tmp.name)/"data"/"tokenscope.sqlite3")
        p.start()
        self.addCleanup(p.stop)
        store.setup()
        with closing(store.connect()) as db,db:
            db.execute("UPDATE profiles SET root=?,auth_action='login' WHERE id=1",(tmp.name,))
            self.profile=dict(db.execute("SELECT * FROM profiles WHERE id=1").fetchone())
        self.flow=login.LoginFlow()
        self.native=FakeClient()
        self.secure=FakeClient()
        self.modes=[]
        def open_client(home,secure=False):
            self.modes.append(secure)
            return self.secure if secure else self.native
        c=patch.object(cloud,"open_client",side_effect=open_client)
        c.start()
        self.addCleanup(c.stop)
        self.synced=[]

    def sync(self,profile_id):
        self.synced.append(profile_id)
        return "同步成功"

    def start(self):
        return self.flow.start(self.profile,self.sync)

    def test_login_success_and_duplicate_click(self):
        result=self.start()
        self.assertEqual(self.modes,[False,True])
        self.assertEqual(self.flow.snapshot()["state"],"waiting")
        with self.assertRaises(ValueError):self.start()
        self.assertFalse(self.flow.cancel("old-ticket"))
        self.secure.logged=True
        self.secure.completions.put({"loginId":"other","success":False})
        self.secure.completions.put({"loginId":"this-flow","success":True})
        self.assertTrue(self.flow.finished.wait(2))
        self.assertEqual(self.flow.snapshot()["state"],"done")
        self.assertEqual(self.synced,[self.profile["id"]])
        self.assertTrue(self.secure.closed)
        self.assertNotIn("url",self.flow.snapshot())
        self.assertIn("url",result)

    def test_cancel_releases_client_and_skips_sync(self):
        result=self.start()
        self.assertTrue(self.flow.cancel(result["ticket"]))
        self.assertTrue(self.flow.finished.wait(2))
        self.assertIn("account/login/cancel",self.secure.calls)
        self.assertTrue(self.secure.closed)
        self.assertEqual(self.flow.snapshot()["state"],"cancelled")
        self.assertEqual(self.synced,[])

    def test_failed_authorization(self):
        self.start()
        self.secure.completions.put({"loginId":"this-flow","success":False})
        self.assertTrue(self.flow.finished.wait(2))
        self.assertEqual(self.flow.snapshot()["state"],"failed")
        self.assertEqual(self.synced,[])

    def test_existing_login_does_not_open_oauth(self):
        self.native.logged=True
        self.assertNotIn("url",self.start())
        self.assertEqual(self.modes,[False])
        self.assertEqual(self.synced,[1])

    def test_unsafe_url_or_ineligible_profile(self):
        for url in ("http://auth.openai.com/a","https://auth.openai.com.evil.test/","https://user@chatgpt.com/","https://chatgpt.com:8081/"):
            with self.subTest(url=url),self.assertRaises(cloud.Unavailable):login.official_url(url)
        self.profile["auth_action"]="install"
        with self.assertRaises(ValueError):self.start()
        self.assertFalse(self.modes)

