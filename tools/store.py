"""Local usage ledger. Each connection is owned by its caller."""
import csv
import hashlib
import io
import json
import os
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

FIELDS = ("event_id", "account", "tool", "model", "timestamp", "input_tokens",
          "output_tokens", "cached_tokens", "cache_write_tokens")
COUNTS = FIELDS[5:]
UNKNOWN = "未知"


def database_path():
    override = os.environ.get("TOKENSCOPE_DATA") or os.environ.get("TOKEN_ATLAS_DATA")
    if override:
        directory = Path(override)
        current = directory / "tokenscope.sqlite3"
        previous = directory / "atlas.sqlite3"
    else:
        local = Path(os.environ.get("LOCALAPPDATA") or Path.home())
        current = local / "TokenScope" / "tokenscope.sqlite3"
        previous = local / "TokenAtlas" / "atlas.sqlite3"
    if previous.is_file() and not current.exists():
        return previous
    return current


DATABASE = database_path()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE, timeout=45)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def setup():
    with closing(connect()) as db, db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS profiles(
          id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, tool TEXT NOT NULL,
          root TEXT NOT NULL COLLATE NOCASE, cloud INTEGER NOT NULL, logs INTEGER NOT NULL,
          enabled INTEGER DEFAULT 1, binding TEXT UNIQUE, summary TEXT, rates TEXT,
          cloud_at TEXT, logs_at TEXT, cloud_status TEXT DEFAULT '等待同步',
          log_status TEXT DEFAULT '等待同步', UNIQUE(tool,root));
        CREATE TABLE IF NOT EXISTS days(profile INTEGER REFERENCES profiles(id), day TEXT,
          tokens INTEGER NOT NULL, PRIMARY KEY(profile,day));
        CREATE TABLE IF NOT EXISTS events(event_id TEXT, account TEXT, tool TEXT, model TEXT,
          timestamp TEXT, input_tokens INTEGER, output_tokens INTEGER, cached_tokens INTEGER,
          cache_write_tokens INTEGER, day TEXT, source TEXT, PRIMARY KEY(account,tool,event_id));
        CREATE INDEX IF NOT EXISTS events_day ON events(day,tool,account,model);
        CREATE TABLE IF NOT EXISTS cursors(profile INTEGER, file TEXT, offset INTEGER,
          signature TEXT, state TEXT, PRIMARY KEY(profile,file));
        """)
        columns={row["name"] for row in db.execute("PRAGMA table_info(profiles)")}
        if "secure_login" not in columns:
            db.execute("ALTER TABLE profiles ADD COLUMN secure_login INTEGER NOT NULL DEFAULT 0")
        if "auth_action" not in columns:
            db.execute("ALTER TABLE profiles ADD COLUMN auth_action TEXT NOT NULL DEFAULT ''")
        for name in ("cloud_attempt","cloud_client","account_hint"):
            if name not in columns:
                db.execute(f"ALTER TABLE profiles ADD COLUMN {name} TEXT")
        if not db.execute("SELECT 1 FROM profiles LIMIT 1").fetchone():
            for name, tool, root, cloud in [
                ("当前 Codex", "Codex", os.environ.get("CODEX_HOME") or Path.home()/".codex", 1),
                ("本机 Claude", "Claude Code", os.environ.get("CLAUDE_CONFIG_DIR") or Path.home()/".claude", 0)]:
                db.execute("INSERT INTO profiles(name,tool,root,cloud,logs) VALUES(?,?,?,?,?)",
                           (name, tool, str(Path(root).resolve()), cloud, 1))


def label(value, field, limit=160):
    if not isinstance(value, str) or not value.strip() or len(value)>limit or any(ord(c)<32 for c in value):
        raise ValueError(f"{field} 必须是 1–{limit} 个可打印字符")
    return value.strip()


def number(value, field):
    if isinstance(value, str) and value.isascii() and value.isdecimal() and len(value)<=16:
        value = int(value)
    if type(value) is not int or not 0 <= value <= 2**53-1:
        raise ValueError(f"{field} 必须是非负安全整数")
    return value


def normalize(row):
    if not isinstance(row, dict):
        raise ValueError("记录必须是对象")
    item = {k:label(row.get(k), k) for k in FIELDS[:5]}
    try:
        ts = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
        if ts.tzinfo is None:
            raise ValueError()
        item["timestamp"] = ts.astimezone(timezone.utc).isoformat()
        item["day"] = ts.astimezone().date().isoformat()
    except (ValueError, OverflowError):
        raise ValueError("timestamp 须包含日期、时间和时区")
    for k in COUNTS:
        item[k] = number(row.get(k, 0 if k == "cache_write_tokens" else None), k)
    if item["cached_tokens"] + item["cache_write_tokens"] > item["input_tokens"]:
        raise ValueError("缓存读取和写入超过输入 Token")
    return item


def save(db, item, source, update=False):
    values = tuple(item[k] for k in FIELDS)+(item["day"],source)
    sql = "INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?)"
    if db.execute(sql, values).rowcount:
        return 1
    key = tuple(item[k] for k in ("account","tool","event_id"))
    old = db.execute("SELECT * FROM events WHERE account=? AND tool=? AND event_id=?",key).fetchone()
    if all(item[k]==old[k] for k in FIELDS):
        return 0
    if update and old["source"]==source:
        # A copied transcript may replay an older partial Claude response.
        if all(item[k]<=old[k] for k in COUNTS):
            return 0
        if not all(item[k]>=old[k] for k in COUNTS):
            raise ValueError("同一消息包含无法比较的用量快照")
        db.execute("UPDATE events SET model=?,timestamp=?,input_tokens=?,output_tokens=?,cached_tokens=?,cache_write_tokens=?,day=? WHERE account=? AND tool=? AND event_id=?",
                   tuple(item[k] for k in (*FIELDS[3:], "day"))+key)
        return 0
    raise ValueError("同一账号、工具和事件 ID 已有不同记录")


def ingest(db, fmt, content):
    content=content.lstrip("\ufeff")
    if fmt=="json":
        rows=json.loads(content)
        if not isinstance(rows,list):
            raise ValueError("JSON 须为明细数组")
    elif fmt=="csv":
        rows=csv.DictReader(io.StringIO(content,newline=""))
        if not set(FIELDS[:-1]).issubset(rows.fieldnames or []):
            raise ValueError("CSV 缺少必要表头")
    else:
        raise ValueError("仅支持 JSON 或 CSV")
    count=added=0
    with db:
        for count,row in enumerate(rows,1):
            try:
                added+=save(db,normalize(row),"import")
            except ValueError as e:
                raise ValueError(f"第 {count} 条记录：{e}") from None
    return {"read":count,"added":added}


def query(db, q, export=False):
    cloud=q.get("view","cloud")=="cloud"
    if cloud:
        table="""(SELECT d.day, d.tokens AS total_tokens,p.name AS account,'Codex' AS tool,
                 '未分模型' AS model, 'cloud' AS source FROM days d JOIN profiles p ON p.id=d.profile)"""
    else:
        table="(SELECT *,input_tokens+output_tokens AS total_tokens FROM events)"
    cond=[]
    args=[]
    for k in ("tool","account","model"):
        if q.get(k):
            cond.append(k+"=?")
            args.append(q[k])
    def where():
        return " WHERE "+" AND ".join(cond) if cond else ""
    def select(cols,tail=""):
        return db.execute(f"SELECT {cols} FROM {table}"+where()+" "+tail,args)
    today=date.today()
    mode=q.get("range","30")
    if mode=="all":
        limits=select("MIN(day), MAX(day)").fetchone()
        start=date.fromisoformat(limits[0]) if limits[0] else today
        end=date.fromisoformat(limits[1]) if limits[1] else today
    elif mode=="custom":
        start=date.fromisoformat(q.get("start",""))
        end=date.fromisoformat(q.get("end",""))
    elif mode in ("7","30","90"):
        start,end=today-timedelta(days=int(mode)-1),today
    else:
        raise ValueError("日期范围无效")
    span=(end-start).days+1
    if not 1<=span<=36600:
        raise ValueError("时间范围必须为 1 至 36600 天")
    cond.append("day BETWEEN ? AND ?")
    args.extend([start.isoformat(),end.isoformat()])
    if export:
        columns="day,account,tool,total_tokens,source" if cloud else ",".join(FIELDS)+",source"
        return [dict(r) for r in select(columns,"ORDER BY day,account"+("" if cloud else ",timestamp,event_id"))]
    grouped={r[0]:r[1] for r in select("day,SUM(total_tokens)","GROUP BY day")}
    daily=[{"day":(start+timedelta(days=i)).isoformat(),"value":grouped.get((start+timedelta(days=i)).isoformat())} for i in range(span)]
    total=sum(grouped.values())
    breakdown=[dict(r) for r in select("account,tool,model,COUNT(*) AS records,SUM(total_tokens) AS tokens",
                  "GROUP BY account,tool,model ORDER BY tokens DESC")]
    parts=None if cloud else dict(select(",".join(f"COALESCE(SUM({k}),0) AS {k}" for k in COUNTS)).fetchone())
    dims={k:[r[0] for r in db.execute(f"SELECT DISTINCT {k} FROM {table} ORDER BY 1")] for k in ("tool","account","model")}
    if cloud:
        dims["account"]=[r[0] for r in db.execute("SELECT name FROM profiles WHERE cloud=1 ORDER BY name")]
        dims["tool"]=["Codex"] if dims["account"] else []
        if not grouped:
            return dict(daily=daily,total=None,average=None,peak=None,active=None,span=span,
                        parts=None,groups=breakdown,dims=dims,start=str(start),end=str(end),reported=0)
    return dict(daily=daily,total=total,average=total/span,peak=max(grouped.values(),default=0),
                active=sum(n>0 for n in grouped.values()),span=span,parts=parts,groups=breakdown,
                dims=dims,start=str(start),end=str(end),reported=len(grouped))


def digest(*parts):
    return hashlib.sha256(json.dumps(parts,ensure_ascii=False).encode()).hexdigest()
