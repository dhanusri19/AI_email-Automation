import datetime, pymysql
from config import Config

def conn():
    return pymysql.connect(host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
        password=Config.DB_PASSWORD, database=Config.DB_NAME, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, autocommit=True)

def _clean(row):
    for k, v in row.items():
        if isinstance(v, datetime.timedelta):
            s = int(v.total_seconds()); row[k] = f"{s//3600:02d}:{(s%3600)//60:02d}"
        elif isinstance(v, datetime.datetime): row[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(v, datetime.date): row[k] = v.isoformat()
    return row

def query(sql, args=(), one=False):
    c = conn()
    try:
        with c.cursor() as cur:
            cur.execute(sql, args)
            rows = [_clean(r) for r in cur.fetchall()]
            return (rows[0] if rows else None) if one else rows
    finally: c.close()

def execute(sql, args=(), rc=False):
    c = conn()
    try:
        with c.cursor() as cur:
            cur.execute(sql, args)
            return cur.rowcount if rc else cur.lastrowid
    finally: c.close()
