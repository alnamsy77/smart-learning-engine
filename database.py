import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("signals.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        ticker TEXT,
        signal TEXT,
        timeframe TEXT,
        price REAL,
        score INTEGER,
        atr REAL,
        atr_pct REAL,
        avg_daily_move REAL,
        target1 REAL,
        target2 REAL,
        target3 REAL,
        rf_state TEXT,
        rqk_state TEXT,
        rp_state TEXT,
        market_state TEXT,
        is_sideways TEXT,
        move_ok TEXT,
        compass_call TEXT,
        compass_put TEXT,
        status TEXT DEFAULT 'OPEN',
        result TEXT DEFAULT 'OPEN',
        raw_json TEXT
    )
    """)
    conn.commit()
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
        created_at, ticker, signal, timeframe, price, score, atr, atr_pct,
        avg_daily_move, target1, target2, target3, rf_state, rqk_state,
        rp_state, market_state, is_sideways, move_ok, compass_call,
        compass_put, status, result, raw_json
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        data.get("ticker") or data.get("السهم"),
        data.get("signal") or data.get("الاتجاه"),
        data.get("timeframe") or data.get("الفريم"),
        to_float(data.get("price") or data.get("السعر")),
        to_int(data.get("score")),
        to_float(data.get("atr")),
        to_float(data.get("atr_pct")),
        to_float(data.get("avg_daily_move")),
        to_float(data.get("target1")),
        to_float(data.get("target2")),
        to_float(data.get("target3")),
        data.get("rf_state"),
        data.get("rqk_state"),
        data.get("rp_state"),
        data.get("market_state"),
        str(data.get("is_sideways")),
        str(data.get("move_ok")),
        str(data.get("compass_call")),
        str(data.get("compass_put")),
        data.get("status", "OPEN"),
        "OPEN",
        str(data)
    ))

    conn.commit()
    inserted_id = cur.lastrowid
    conn.close()
    return inserted_id

def fetch_recent(limit=100):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return rows

def fetch_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) AS c FROM signals").fetchone()["c"]
    call_count = conn.execute("SELECT COUNT(*) AS c FROM signals WHERE signal='CALL'").fetchone()["c"]
    put_count = conn.execute("SELECT COUNT(*) AS c FROM signals WHERE signal='PUT'").fetchone()["c"]
    open_count = conn.execute("SELECT COUNT(*) AS c FROM signals WHERE result='OPEN'").fetchone()["c"]

    by_ticker = conn.execute("""
        SELECT ticker, COUNT(*) AS count_signals, ROUND(AVG(score), 2) AS avg_score
        FROM signals
        GROUP BY ticker
        ORDER BY count_signals DESC
        LIMIT 10
    """).fetchall()

    by_market = conn.execute("""
        SELECT market_state, COUNT(*) AS count_signals, ROUND(AVG(score), 2) AS avg_score
        FROM signals
        GROUP BY market_state
        ORDER BY count_signals DESC
    """).fetchall()

    conn.close()
    return {
        "total": total,
        "call_count": call_count,
        "put_count": put_count,
        "open_count": open_count,
        "by_ticker": by_ticker,
        "by_market": by_market,
    }
