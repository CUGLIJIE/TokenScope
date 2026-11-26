"""A single browser sign-in on Codex's own loopback callback listener."""
import queue
import threading
import time
import uuid
from contextlib import closing
from pathlib import Path
from urllib.parse import urlsplit

from . import cloud, store


def official_url(value):
    parts=urlsplit(value)
    if (parts.scheme!="https" or parts.hostname not in {"auth.openai.com","chatgpt.com"}
            or parts.username is not None or parts.password is not None or parts.port not in (443,None)):
        raise cloud.Unavailable("客户端返回了无法识别的登录地址，请更新 Codex 后重试")
    return value


class LoginFlow:
    active_states={"starting","waiting","syncing"}

    def __init__(self):
        self.lock=threading.Lock()
        self.stop=threading.Event()
        self.task={}
        self.finished=threading.Event()
        self.finished.set()

    def snapshot(self):
        with self.lock:
            return dict(self.task)

    def update(self,state,message):
        with self.lock:
            self.task.update(state=state,message=message)
            if state not in self.active_states:
                self.finished.set()

    def cancel(self,ticket):
        with self.lock:
            if self.task.get("ticket")==ticket and self.task.get("state") in ("starting","waiting"):
                self.stop.set()
                return True
            return False

    def start(self,profile,on_success):
        if not (profile["enabled"] and profile["tool"]=="Codex" and profile["cloud"] and profile["auth_action"]=="login"):
            raise ValueError("请先同步并选择需要登录的 Codex 云端账号")
        with self.lock:
            if self.task.get("state") in self.active_states:
                raise ValueError("已有登录正在进行，请完成或取消后再试")
            ticket=uuid.uuid4().hex
            self.task=dict(ticket=ticket,profile=profile["id"],state="starting",message="正在连接 Codex…")
            self.stop.clear()
            self.finished.clear()
        client=None
        login_id=None
        try:
            Path(profile["root"]).mkdir(parents=True,exist_ok=True)
            # Recheck the current native sign-in before starting a browser login.
            if not profile["secure_login"]:
                with closing(cloud.open_client(profile["root"])) as existing:
                    try:
                        cloud.identity(existing)
                    except cloud.LoginRequired:
                        pass
                    else:
                        self.update("syncing","已检测到登录，正在同步…")
                        message=on_success(profile["id"])
                        self.update("done",message)
                        return {"ticket":ticket}
            client=cloud.open_client(profile["root"],secure=True)
            try:
                cloud.identity(client)
            except cloud.LoginRequired:
                result=client.call("account/login/start",{"type":"chatgpt"})
                login_id=result.get("loginId")
                if not isinstance(login_id,str) or not login_id:
                    raise cloud.Unavailable("客户端未返回有效登录会话")
                url=official_url(result.get("authUrl",""))
            with closing(store.connect()) as db,db:
                db.execute("UPDATE profiles SET secure_login=1 WHERE id=?",(profile["id"],))
            self.update("waiting" if login_id else "syncing","请在官方页面完成登录。" if login_id else "已检测到登录，正在同步…")
            worker=threading.Thread(target=self.monitor,args=(client,login_id,profile["id"],on_success),daemon=True)
            worker.start()
            client=None  # Ownership transferred to the monitor.
            return {"ticket":ticket,"url":url} if login_id else {"ticket":ticket}
        except Exception as exc:
            if client:
                client.close()
            msg=str(exc) if isinstance(exc,cloud.Unavailable) else "无法启动登录，请检查 Codex 版本和配置目录权限"
            self.update("failed",msg)
            raise ValueError(msg) from None

    def monitor(self,client,login_id,profile_id,on_success):
        state,message="failed","登录未完成，请重试"
        try:
            if login_id:
                deadline=time.monotonic()+300
                while not self.stop.is_set() and time.monotonic()<deadline:
                    try:
                        result=client.completions.get(timeout=.25)
                    except queue.Empty:
                        continue
                    if result is None:
                        raise cloud.Unavailable("Codex 登录连接已关闭")
                    if result.get("loginId")!=login_id:
                        continue
                    if result.get("success") is not True:
                        raise cloud.Unavailable("官方登录未完成，请重试并检查系统凭据存储")
                    break
                else:
                    client.call("account/login/cancel",{"loginId":login_id})
                    state="cancelled"
                    message="已取消登录。" if self.stop.is_set() else "登录已超时，请重新打开登录窗口。"
                    return
            cloud.identity(client)
            self.update("syncing","登录成功，正在同步账号用量…")
            message=on_success(profile_id)
            state="done"
        except Exception as exc:
            if isinstance(exc,cloud.Unavailable):
                message=str(exc)
        finally:
            try:
                client.close()
            finally:
                self.update(state,message)

