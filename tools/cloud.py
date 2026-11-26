"""Codex App Server transport and usage collection."""
import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from .store import digest, number, now

INSTALL_HINT="未找到可用的本机 Codex 客户端。请安装 ChatGPT Windows 桌面版，打开一次后重新检测。"


class Unavailable(Exception):
    pass


class LoginRequired(Unavailable):
    pass


class MissingClient(Unavailable):
    pass


class UnsupportedMethod(Unavailable):
    pass


class ClientFailure(Unavailable):
    """The local binary or its protocol transport failed."""


def diagnostic(stage,exc):
    if isinstance(exc,Unavailable):
        return str(exc)
    win=getattr(exc,"winerror",None)
    if win:
        hint={2:"文件不存在",3:"路径不存在",5:"Windows 拒绝访问。请打开或更新桌面版后重新检测；若仍受限，请检查客户端路径和设备的应用运行策略",193:"程序格式或架构不兼容",
              216:"程序与此 Windows 版本不兼容",740:"启动被权限设置阻止"}.get(win,"Windows 调用失败")
        return f"{stage}：{hint}（WinError {win}）"
    trace=exc.__traceback__
    location=""
    while trace:
        filename=Path(trace.tb_frame.f_code.co_filename).name
        if filename in {"cloud.py","store.py","app.py"}:
            location=f" · {filename}:{trace.tb_lineno}"
        trace=trace.tb_next
    return f"{stage}失败（{type(exc).__name__}{location}）"


def powershell(script, **kwargs):
    shell=Path(os.environ.get("SystemRoot","C:/Windows"))/"System32/WindowsPowerShell/v1.0/powershell.exe"
    # The parent may be PowerShell 7; use Windows PowerShell's own system modules.
    command="$env:PSModulePath=[IO.Path]::Combine($PSHOME,'Modules'); "+script
    return subprocess.run([str(shell),"-NoProfile","-NonInteractive","-Command",command],
        stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding="utf-8",errors="replace",
        timeout=20,creationflags=subprocess.CREATE_NO_WINDOW,**kwargs)


@lru_cache(maxsize=12)
def _openai_signature(path,size,mtime_ns):
    # File metadata is part of the key so desktop updates are verified again.
    result=powershell(
        "$ErrorActionPreference='Stop'; "
        "$s=Get-AuthenticodeSignature -LiteralPath $env:TOKENSCOPE_VERIFY_FILE; "
        "if ($s.Status -eq 'Valid' -and $s.SignerCertificate.GetNameInfo('SimpleName',$false) "
        "-in @('OpenAI OpCo, LLC','OpenAI, L.L.C.','OpenAI, LLC')) {exit 0}; exit 1",
        env={**os.environ,"TOKENSCOPE_VERIFY_FILE":str(path)})
    return result.returncode==0


def desktop_user_clients(root):
    files=[]
    for file in (root/"codex.exe",*root.glob("*/codex.exe")):
        try:
            if file.is_file():
                stat=file.stat()
                files.append((stat.st_mtime_ns,file,stat.st_size))
        except OSError:
            continue
    for mtime,path,size in sorted(files,reverse=True):
        try:
            if _openai_signature(path,size,mtime):
                yield str(path)
        except (OSError,subprocess.TimeoutExpired):
            continue


def candidates():
    override=os.environ.get("TOKENSCOPE_CODEX") or os.environ.get("TOKEN_ATLAS_CODEX")
    if override:
        if Path(override).is_file():
            yield override
        return
    desktop_root=None
    if os.name=="nt" and os.environ.get("LOCALAPPDATA"):
        desktop_root=Path(os.environ["LOCALAPPDATA"])/"OpenAI"/"Codex"/"bin"
        yield from desktop_user_clients(desktop_root)
    cli=shutil.which("codex.exe" if os.name=="nt" else "codex")
    if cli and not (desktop_root and Path(cli).is_relative_to(desktop_root)):
        yield cli
    if os.name=="nt":
        try:
            found=powershell("[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); (Get-AppxPackage -Name OpenAI.Codex | Select-Object -First 1).InstallLocation")
        except (OSError,subprocess.TimeoutExpired):
            return
        base=found.stdout.strip()
        desktop=Path(base)/"app"/"resources"/"codex.exe"
        if base and desktop.is_file() and (not cli or Path(cli).resolve()!=desktop.resolve()):
            yield str(desktop)


def rpc_error(method,error):
    code=error.get("code")
    detail=str(error.get("message","")).lower()
    if code==-32601:
        return UnsupportedMethod(f"此 Codex 版本不支持 {method}（-32601），请更新 Codex 后重试")
    for http,hint in ((401,"登录已失效，请在 Codex 重新登录"),(403,"服务拒绝访问，请核对登录账号和工作区权限"),(429,"服务限流，请稍后重试")):
        if code==http or re.search(rf"\b{http}\b",detail):
            return Unavailable(f"{method}：{hint}（HTTP {http}）")
    if any(x in detail for x in ("timed out","timeout","connection refused","connection reset","dns","proxy","certificate","error sending request")):
        return Unavailable(f"{method} 连接失败，请检查新电脑的网络、系统时间和代理设置（{code}）")
    return Unavailable(f"{method} 查询失败（{code}），请检查客户端、账号和网络后重试")


class Client:
    def __init__(self, home, secure=False, exe=None):
        exe=exe or next(candidates(),None)
        if not exe:
            raise MissingClient(INSTALL_HINT)
        if not Path(home).is_dir():
            raise LoginRequired("尚未创建 Codex 配置目录，请登录 ChatGPT")
        options=["-c",'cli_auth_credentials_store="keyring"'] if secure else []
        command=[exe,*options]
        if Path(exe).name.lower()!="codex-app-server.exe":
            command.append("app-server")
        self.proc=subprocess.Popen(command,stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding="utf-8",errors="replace",
            env={**os.environ,"CODEX_HOME":str(home)},creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        self.messages=queue.Queue()
        self.completions=queue.Queue()
        self.seq=0
        self.reader=threading.Thread(target=self.read,daemon=True)
        self.reader.start()

    def read(self):
        try:
            for line in self.proc.stdout:
                try:
                    msg=json.loads(line)
                    if isinstance(msg,dict) and "id" in msg:
                        self.messages.put(msg)
                    elif isinstance(msg,dict) and msg.get("method")=="account/login/completed":
                        self.completions.put(msg.get("params") or {})
                except ValueError:
                    pass
        finally:
            self.messages.put(None)
            self.completions.put(None)

    def send(self,msg):
        try:
            self.proc.stdin.write(json.dumps(msg)+"\n")
            self.proc.stdin.flush()
        except OSError as exc:
            raise ClientFailure(diagnostic("连接 Codex 子进程",exc)) from exc

    def call(self,method,params):
        self.seq+=1
        self.send(dict(method=method,params=params,id=self.seq))
        deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            try:
                msg=self.messages.get(timeout=max(.01,deadline-time.monotonic()))
            except queue.Empty:
                break
            if msg is None:
                raise ClientFailure(f"执行 {method} 时 Codex 已退出（退出码 {self.proc.poll()}），请检查客户端能否正常启动")
            if msg.get("id")!=self.seq:
                continue
            if "error" in msg:
                raise rpc_error(method,msg["error"])
            result=msg.get("result")
            if not isinstance(result,dict):
                raise Unavailable(f"{method} 响应格式不受支持")
            return result
        raise Unavailable(f"{method} 等待超时")

    def close(self):
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        try:
            self.proc.wait(2)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.reader.join(2)
        self.proc.stdout.close()


def identity(client):
    record=client.call("account/read",{"refreshToken":False})
    account=record.get("account") or {}
    if not account:
        raise LoginRequired("此配置目录尚未登录 ChatGPT")
    if account.get("type")!="chatgpt":
        raise Unavailable("此配置目录使用其他登录方式，请为 ChatGPT 使用独立目录")
    routing=record.get("workspaceRouting") or {}
    workspace=routing.get("chatgptAccountId") or account.get("workspaceName") or ""
    email=account.get("email")
    if not email:
        raise Unavailable("无法核对账号身份")
    name,_,domain=email.partition("@")
    client.account_hint=name[:1]+"***"+("@"+domain if domain else "")+(" · "+account["workspaceName"] if account.get("workspaceName") else "")
    return digest(email.casefold(),workspace),digest(routing.get("chatgptAccountId")) if routing.get("chatgptAccountId") else None


def daily_rows(result):
    rows=result.get("dailyUsageBuckets")
    if rows is not None and not isinstance(rows,list):
        raise Unavailable("云端日汇总格式不受支持")
    values={}
    for row in rows or []:
        try:
            stamp=row["startDate"]
            day=(datetime.fromisoformat(stamp.replace("Z","+00:00")).date() if isinstance(stamp,str) and "T" in stamp else date.fromisoformat(stamp)).isoformat()
            values[day]=number(row["tokens"],"tokens")
        except (ValueError,TypeError,KeyError) as exc:
            raise Unavailable("云端已应答，但每日记录中的日期或 Token 数格式不受支持（account/usage/read）") from exc
    summary=result.get("summary")
    if not isinstance(summary,dict):
        raise Unavailable("用量接口返回了未知的数据格式，请更新 Codex 并重试")
    summary={k:number(summary[k],k) for k in ("lifetimeTokens","peakDailyTokens","currentStreakDays","longestStreakDays","longestRunningTurnSec") if summary.get(k) is not None}
    return list(values.items()),summary


def open_client(home, secure=False, exe=None):
    if exe is None:
        failure=None
        for candidate in candidates():
            try:
                return open_client(home,secure,candidate)
            except ClientFailure as exc:
                failure=exc
        if failure:
            raise failure
        raise MissingClient(INSTALL_HINT)
    try:
        client=Client(home,secure,exe)
    except OSError as exc:
        raise ClientFailure(diagnostic("启动 Codex 客户端",exc)) from exc
    try:
        info=client.call("initialize",{"clientInfo":{"name":"tokenscope","version":"1.4"},"capabilities":{}})
        versions=re.findall(r"/(\d+\.\d+\.\d+[\w.+-]*)",info.get("userAgent",""))
        client.version=versions[0] if versions else "版本未知"
        client.send({"method":"initialized"})
        return client
    except Exception:
        client.close()
        raise


def collect(db,profile):
    error=None
    for exe in candidates():
        with db:
            db.execute("UPDATE profiles SET cloud_client=? WHERE id=?",(exe,profile["id"]))
        try:
            return collect_with_client(db,profile,exe)
        except (UnsupportedMethod,ClientFailure) as exc:
            error=exc
            profile=db.execute("SELECT * FROM profiles WHERE id=?",(profile["id"],)).fetchone()
    if error:
        raise error
    raise MissingClient(INSTALL_HINT)


def collect_with_client(db,profile,exe):
    client=open_client(profile["root"],bool(profile["secure_login"]),exe)
    try:
        try:
            owner,workspace=identity(client)
        except LoginRequired:
            if not profile["secure_login"]:
                raise
            # Also recognize a later sign-in performed directly in Codex.
            client.close()
            client=open_client(profile["root"],False,exe)
            owner,workspace=identity(client)
        if profile["binding"] and owner!=profile["binding"]:
            raise Unavailable("登录账号已切换，请使用该账号独立的配置目录")
        if db.execute("SELECT 1 FROM profiles WHERE binding=? AND id<>?",(owner,profile["id"])).fetchone():
            raise Unavailable("此登录账号已关联其他配置，跳过重复同步")
        with db:
            db.execute("UPDATE profiles SET account_hint=?,cloud_client=? WHERE id=?",
                       (client.account_hint,f"{client.version} · {exe}",profile["id"]))
        cloud_at=profile["cloud_at"]
        unsupported=None
        try:
            usage=client.call("account/usage/read",{})
            rows,summary=daily_rows(usage)
            status=f"已获取 {len(rows)} 个日期" if rows else "已连接云端；服务端本次未提供每日记录"
            cloud_at=now()
        except (Unavailable,ValueError,TypeError,KeyError) as e:
            rows=[]
            summary=json.loads(profile["summary"] or "{}")
            status=diagnostic("解析账号云端汇总",e)
            if isinstance(e,UnsupportedMethod):
                unsupported=e
        try:
            r=client.call("account/rateLimits/read",{"excludeResetCreditDetails":True}).get("rateLimits") or {}
            rates={k:{f:v for f,v in r[k].items() if f in ("usedPercent","windowDurationMins","resetsAt")}
                   for k in ("primary","secondary") if isinstance(r.get(k),dict)}
            rates["updated_at"]=now()
        except (Unavailable,ValueError,TypeError,KeyError,AttributeError) as e:
            rates=json.loads(profile["rates"] or "{}")
            rates["error"]=diagnostic("解析额度快照",e)
        if identity(client)[0]!=owner:
            raise Unavailable("同步期间登录身份发生变化")
        if workspace:
            summary["workspace_digest"]=workspace
        with db:
            db.executemany("INSERT INTO days VALUES(?,?,?) ON CONFLICT(profile,day) DO UPDATE SET tokens=excluded.tokens",
                           [(profile["id"],d,v) for d,v in rows])
            db.execute("UPDATE profiles SET auth_action='',binding=?,summary=?,rates=?,cloud_at=?,cloud_status=? WHERE id=?",
                (owner,json.dumps(summary),json.dumps(rates),cloud_at,status,profile["id"]))
        if unsupported:
            raise unsupported
    finally:
        client.close()
