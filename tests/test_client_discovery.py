import os
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from tools import cloud


class ClientDiscoveryTests(unittest.TestCase):
    def test_user_installation_is_rediscovered_and_signatures_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as contexts:
            root=Path(tmp)/"OpenAI"/"Codex"/"bin"
            contexts.enter_context(patch.dict(os.environ,{"TOKENSCOPE_CODEX":"","TOKEN_ATLAS_CODEX":"","LOCALAPPDATA":tmp}))
            contexts.enter_context(patch.object(cloud.shutil,"which",return_value=None))
            contexts.enter_context(patch.object(cloud,"powershell",return_value=type("Result",(),{"stdout":""})()))
            contexts.enter_context(patch.object(cloud,"_openai_signature",side_effect=lambda path,*args:path.parent.name!="unsigned"))
            self.assertEqual(list(cloud.candidates()),[])
            for n in ("first","second","unsigned"):
                file=root/n/"codex.exe"
                file.parent.mkdir(parents=True)
                file.write_bytes(b"fixture")
            os.utime(root/"first"/"codex.exe",(1000,1000))
            expected=[str(root/n/"codex.exe") for n in ("second","first")]
            self.assertEqual(list(cloud.candidates()),expected)

    def test_login_can_use_next_startable_client(self):
        opened=[]
        class Client:
            def __init__(self,home,secure,exe):
                opened.append((exe,secure))
                if exe=="denied":
                    e=PermissionError()
                    e.winerror=5
                    raise e
            def call(self,method,params):
                return {"userAgent":"codex/0.172.0"}
            def send(self,msg):
                pass
        with patch.object(cloud,"candidates",return_value=["denied","allowed"]),patch.object(cloud,"Client",Client):
            client=cloud.open_client("example-home",secure=True)
        self.assertEqual(opened,[("denied",True),("allowed",True)])
        self.assertEqual(client.version,"0.172.0")

