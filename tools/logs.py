"""Streaming JSONL adapters. Checkpoints contain only numeric/context metadata."""
import json
from pathlib import Path
from .store import UNKNOWN, digest, normalize, number, now, save

MAX_LINE=16*1024*1024


def usage_counts(u):
    return [number(u[k],k) for k in ("input_tokens","output_tokens")] + [number(u.get("cached_input_tokens",0),"cached_input_tokens")]


def codex(row,s):
    kind=row.get("type")
    p=row.get("payload") or {}
    if kind=="session_meta":
        s["session"]=p.get("id") or p.get("session_id") or s["session"]
        s["workspace"]=digest(p["creator_account_id"]) if p.get("creator_account_id") else None
        # Fork rollouts can replay earlier turns from a parent. Do not charge inherited prefixes.
        s["fork"]=bool(p.get("forked_from_id") or p.get("parent_thread_id"))
    if kind=="turn_context":
        s["model"]=p.get("model") or UNKNOWN
    if kind!="event_msg" or p.get("type")!="token_count" or not p.get("info"):
        return
    info=p["info"]
    cumulative=info.get("total_token_usage")
    last=info.get("last_token_usage")
    if cumulative:
        current=usage_counts(cumulative)
        previous=s.get("cumulative")
        if current==previous:
            return
        s["cumulative"]=current
        if previous and all(a>=b for a,b in zip(current,previous)):
            counts=[a-b for a,b in zip(current,previous)]
        else:
            counts=usage_counts(last) if last else current
        key=digest("codex",s["session"],row["timestamp"],current)
    elif last:
        counts=usage_counts(last)
        key=digest("codex",s["session"],row["timestamp"],row.get("ordinal"),counts)
    else:
        return
    if s.get("fork"):
        return
    return dict(event_id=key,model=s.get("model",UNKNOWN),timestamp=row["timestamp"],
                input_tokens=counts[0],output_tokens=counts[1],cached_tokens=counts[2])


def claude(row,s):
    if row.get("type")!="assistant":
        return
    msg=row.get("message") or {}
    u=msg.get("usage")
    if not u or not msg.get("id"):
        return
    if msg.get("model")=="<synthetic>":
        return
    read=number(u.get("cache_read_input_tokens",0),"cache_read_input_tokens")
    write=number(u.get("cache_creation_input_tokens",0),"cache_creation_input_tokens")
    return dict(event_id=digest("claude",msg["id"],row.get("requestId")),model=msg.get("model") or UNKNOWN,
                timestamp=row["timestamp"],input_tokens=number(u["input_tokens"],"input_tokens")+read+write,
                output_tokens=number(u["output_tokens"],"output_tokens"),cached_tokens=read,cache_write_tokens=write)


ADAPTERS={"Codex":(codex,("sessions","archived_sessions")),"Claude Code":(claude,("projects",))}


def scan_file(db,profile,path,parse,workspace):
    checkpoint=db.execute("SELECT * FROM cursors WHERE profile=? AND file=?",(profile["id"],str(path))).fetchone()
    with path.open("rb") as f:
        signature=digest(f.readline(4096).hex())
        size=path.stat().st_size
        valid=checkpoint and checkpoint["signature"]==signature and checkpoint["offset"]<=size
        if valid and checkpoint["offset"]==size:
            return 0,0
        state=json.loads(checkpoint["state"]) if valid else {"session":digest(path.name)}
        f.seek(checkpoint["offset"] if valid else 0)
        added=invalid=0
        with db:
            while f.tell()<size:
                offset=f.tell()
                line=f.readline(MAX_LINE+1)
                if len(line)>MAX_LINE:
                    while line and not line.endswith(b"\n"):
                        line=f.readline(MAX_LINE)
                    if not line.endswith(b"\n"):
                        f.seek(offset)
                        break
                    invalid+=1
                    continue
                if not line.endswith(b"\n"):
                    f.seek(offset)
                    break
                try:
                    row=json.loads(line)
                    item=parse(row,state)
                    if item and not (workspace and state.get("workspace") and workspace!=state["workspace"]):
                        added+=save(db,normalize(dict(item,account=profile["name"],tool=profile["tool"])),
                                    "local",update=parse is claude)
                except (ValueError,KeyError,TypeError,AttributeError,OverflowError):
                    invalid+=1
            db.execute("INSERT OR REPLACE INTO cursors VALUES(?,?,?,?,?)",(profile["id"],str(path),f.tell(),signature,json.dumps(state)))
    return added,invalid


def collect(db,profile):
    parse,dirs=ADAPTERS[profile["tool"]]
    root=Path(profile["root"])
    workspace=(json.loads(profile["summary"] or "{}")).get("workspace_digest")
    files=added=skips=0
    for name in dirs:
        for path in (root/name).rglob("*.jsonl"):
            try:
                n,e=scan_file(db,profile,path,parse,workspace)
                files+=1
                added+=n
                skips+=e
            except OSError:
                skips+=1
    with db:
        db.execute("UPDATE profiles SET logs_at=?,log_status=? WHERE id=?",
           (now(),f"{files} 个文件 · 新增 {added} 条 · 跳过异常 {skips} 处",profile["id"]))
