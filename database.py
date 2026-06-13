import os
import json
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing. Add it in Render Environment Variables.")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def pct(part, total):
    try:
        return round((part / total) * 100, 1) if total > 0 else 0
    except Exception:
        return 0


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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS learning_insights (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        insight_key TEXT UNIQUE,
        insight_type TEXT,
        title TEXT,
        value NUMERIC,
        details JSONB
    );
    """)

    cur.execute("""
    ALTER TABLE signals
    ADD COLUMN IF NOT EXISTS trade_id TEXT,
    ADD COLUMN IF NOT EXISTS event TEXT DEFAULT 'OPEN',
    ADD COLUMN IF NOT EXISTS stop_loss NUMERIC,
    ADD COLUMN IF NOT EXISTS target1_hit BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS target2_hit BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS target3_hit BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS target1_hit_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS target2_hit_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS target3_hit_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_signals_trade_id
    ON signals (trade_id);
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


def normalize_event(data):
    event = data.get("event") or data.get("status") or "OPEN"
    return str(event).upper()


def build_trade_id(data):
    trade_id = data.get("trade_id")
    if trade_id:
        return str(trade_id)

    ticker = data.get("ticker") or data.get("السهم") or "UNKNOWN"
    timeframe = data.get("timeframe") or data.get("الفريم") or "NA"
    signal = data.get("signal") or data.get("الاتجاه") or "NA"
    price = data.get("price") or data.get("السعر") or "NA"

    return f"{ticker}_{timeframe}_{signal}_{price}"


def update_trade_event(data: dict):
    trade_id = build_trade_id(data)
    event = normalize_event(data)

    conn = get_conn()
    cur = conn.cursor()

    if event == "TARGET1_HIT":
        cur.execute("""
        UPDATE signals
        SET
            event = %s,
            status = 'TARGET1_HIT',
            result = 'WIN',
            target1_hit = TRUE,
            target1_hit_at = COALESCE(target1_hit_at, NOW()),
            raw_json = %s
        WHERE trade_id = %s
        RETURNING id;
        """, (event, json.dumps(data, ensure_ascii=False), trade_id))

    elif event == "TARGET2_HIT":
        cur.execute("""
        UPDATE signals
        SET
            event = %s,
            status = 'TARGET2_HIT',
            result = 'WIN',
            target1_hit = TRUE,
            target2_hit = TRUE,
            target1_hit_at = COALESCE(target1_hit_at, NOW()),
            target2_hit_at = COALESCE(target2_hit_at, NOW()),
            raw_json = %s
        WHERE trade_id = %s
        RETURNING id;
        """, (event, json.dumps(data, ensure_ascii=False), trade_id))

    elif event == "TARGET3_HIT":
        cur.execute("""
        UPDATE signals
        SET
            event = %s,
            status = 'TARGET3_HIT',
            result = 'WIN',
            target1_hit = TRUE,
            target2_hit = TRUE,
            target3_hit = TRUE,
            target1_hit_at = COALESCE(target1_hit_at, NOW()),
            target2_hit_at = COALESCE(target2_hit_at, NOW()),
            target3_hit_at = COALESCE(target3_hit_at, NOW()),
            closed_at = COALESCE(closed_at, NOW()),
            raw_json = %s
        WHERE trade_id = %s
        RETURNING id;
        """, (event, json.dumps(data, ensure_ascii=False), trade_id))

    elif event == "LOSS":
        cur.execute("""
        UPDATE signals
        SET
            event = %s,
            status = 'LOSS',
            result = 'LOSS',
            closed_at = COALESCE(closed_at, NOW()),
            raw_json = %s
        WHERE trade_id = %s
        RETURNING id;
        """, (event, json.dumps(data, ensure_ascii=False), trade_id))

    else:
        cur.close()
        conn.close()
        return None

    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if row:
        return row["id"]
    return None


def insert_signal(data: dict):
    event = normalize_event(data)

    if event in ["TARGET1_HIT", "TARGET2_HIT", "TARGET3_HIT", "LOSS"]:
        updated_id = update_trade_event(data)
        if updated_id:
            return updated_id

    trade_id = build_trade_id(data)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO signals (
        trade_id, event, ticker, signal, timeframe, price, score, atr, atr_pct,
        avg_daily_move, target1, target2, target3, stop_loss,
        rf_state, rqk_state, rp_state, market_state, is_sideways, move_ok,
        compass_call, compass_put, indicator, status, result, raw_json
    )
    VALUES (
        %(trade_id)s, %(event)s, %(ticker)s, %(signal)s, %(timeframe)s, %(price)s,
        %(score)s, %(atr)s, %(atr_pct)s, %(avg_daily_move)s,
        %(target1)s, %(target2)s, %(target3)s, %(stop_loss)s,
        %(rf_state)s, %(rqk_state)s, %(rp_state)s, %(market_state)s,
        %(is_sideways)s, %(move_ok)s, %(compass_call)s, %(compass_put)s,
        %(indicator)s, %(status)s, %(result)s, %(raw_json)s
    )
    RETURNING id;
    """, {
        "trade_id": trade_id,
        "event": event,
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
        "stop_loss": to_float(data.get("stop_loss")),
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


def best_group(cur, column):
    cur.execute(f"""
        SELECT
            {column} AS name,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE result = 'WIN') AS wins,
            COUNT(*) FILTER (WHERE result = 'LOSS') AS losses,
            COUNT(*) FILTER (WHERE target1_hit = TRUE) AS target1_hits,
            ROUND(
                CASE
                    WHEN COUNT(*) FILTER (WHERE result IN ('WIN','LOSS')) > 0
                    THEN (COUNT(*) FILTER (WHERE result = 'WIN')::numeric /
                          COUNT(*) FILTER (WHERE result IN ('WIN','LOSS'))::numeric) * 100
                    ELSE 0
                END, 1
            ) AS win_rate
        FROM signals
        WHERE {column} IS NOT NULL
          AND {column}::text <> ''
        GROUP BY {column}
        ORDER BY win_rate DESC, wins DESC, target1_hits DESC, total DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if not row:
        return {"name": "-", "win_rate": 0, "total": 0, "wins": 0, "losses": 0, "target1_hits": 0}
    return dict(row)


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

    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE result='WIN'")
    win_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE result='LOSS'")
    loss_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE target1_hit = TRUE")
    target1_hit = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE target2_hit = TRUE")
    target2_hit = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE target3_hit = TRUE")
    target3_hit = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE signal='CALL' AND result='WIN'")
    call_wins = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE signal='CALL' AND result IN ('WIN','LOSS')")
    call_closed = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE signal='PUT' AND result='WIN'")
    put_wins = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM signals WHERE signal='PUT' AND result IN ('WIN','LOSS')")
    put_closed = cur.fetchone()["c"]

    best_score = best_group(cur, "score")
    best_market_state = best_group(cur, "market_state")
    best_timeframe = best_group(cur, "timeframe")
    best_ticker = best_group(cur, "ticker")

    cur.close()
    conn.close()

    return {
        "total": total,
        "call_count": call_count,
        "put_count": put_count,
        "open_count": open_count,
        "win_count": win_count,
        "loss_count": loss_count,
        "target1_hit": target1_hit,
        "target2_hit": target2_hit,
        "target3_hit": target3_hit,
        "call_win_rate": pct(call_wins, call_closed),
        "put_win_rate": pct(put_wins, put_closed),
        "best_score": best_score,
        "best_market_state": best_market_state,
        "best_timeframe": best_timeframe,
        "best_ticker": best_ticker,
    }


def save_learning_insight(insight_key, insight_type, title, value, details):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO learning_insights (
            insight_key,
            insight_type,
            title,
            value,
            details
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (insight_key)
        DO UPDATE SET
            created_at = NOW(),
            insight_type = EXCLUDED.insight_type,
            title = EXCLUDED.title,
            value = EXCLUDED.value,
            details = EXCLUDED.details;
    """, (
        insight_key,
        insight_type,
        title,
        value,
        json.dumps(details, ensure_ascii=False)
    ))

    conn.commit()
    cur.close()
    conn.close()


def get_learning_insights():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM learning_insights
        ORDER BY created_at DESC;
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows
