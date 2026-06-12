import os
import json
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing. Add it in Render Environment Variables.")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        ticker TEXT,
        signal TEXT,
        timeframe TEXT,
        price NUMERIC,
        score INTEGER,
        atr NUMERIC,
        atr_pct NUMERIC,
        avg_daily_move NUMERIC,
        target1 NUMERIC,
        target2 NUMERIC,
        target3 NUMERIC,
        rf_state TEXT,
        rqk_state TEXT,
        rp_state TEXT,
        market_state TEXT,
        is_sideways TEXT,
        move_ok TEXT,
        compass_call TEXT,
        compass_put TEXT,
        indicator TEXT,
        status TEXT DEFAULT 'OPEN',
        result TEXT DEFAULT 'OPEN',
        raw_json JSONB
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def to_float(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default

def to_int(value, default=None):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default

def insert_signal(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO signals (
        ticker, signal, timeframe, price, score, atr, atr_pct,
        avg_daily_move, target1, target2, target3, rf_state, rqk_state,
        rp_state, market_state, is_sideways, move_ok, compass_call,
        compass_put, indicator, status, result, raw_json
    )
    VALUES (
        %(ticker)s, %(signal)s, %(timeframe)s, %(price)s, %(score)s, %(atr)s, %(atr_pct)s,
        %(avg_daily_move)s, %(target1)s, %(target2)s, %(target3)s, %(rf_state)s, %(rqk_state)s,
        %(rp_state)s, %(market_state)s, %(is_sideways)s, %(move_ok)s, %(compass_call)s,
        %(compass_put)s, %(indicator)s, %(status)s, %(result)s, %(raw_json)s
    )
    RETURNING id;
    """, {
        "ticker": data.get("ticker") or data.get("السهم"),
        "signal": data.get("signal") or data.get("الاتجاه"),
        "timeframe": data.get("timeframe") or data.get("الفريم"),
        "price": to_float(data.get("price") or data.get("السعر")),
        "score": to_int(data.get("score")),
        "atr": to_float(data.get("atr")),
        "atr_pct": to_float(data.get("atr_pct")),
        "avg_daily_move": to_float(data.get("avg_daily_move")),
        "target1": to_float(data.get("target1")),
        "target2": to_float(data.get("target2")),
        "target3": to_float(data.get("target3")),
        "rf_state": data.get("rf_state"),
        "rqk_state": data.get("rqk_state"),
        "rp_state": data.get("rp_state"),
        "market_state": data.get("market_state"),
        "is_sideways": str(data.get("is_sideways")),
        "move_ok": str(data.get("move_ok")),
        "compass_call": str(data.get("compass_call")),
        "compass_put": str(data.get("compass_put")),
        "indicator": data.get("indicator"),
        "status": data.get("status", "OPEN"),
        "result": "OPEN",
        "raw_json": json.dumps(data, ensure_ascii=False)
    })
    inserted_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return inserted_id

def fetch_recent(limit=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM signals ORDER BY id DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def fetch_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM signals")
    total = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE signal='CALL'")
    call_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE signal='PUT'")
    put_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE result='OPEN'")
    open_count = cur.fetchone()["c"]
    cur.close()
    conn.close()
    return {
        "total": total,
        "call_count": call_count,
        "put_count": put_count,
        "open_count": open_count,
    }
