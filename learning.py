from database import (
    fetch_recent,
    save_learning_insight
)

def simple_learning_summary():
    rows = fetch_recent(500)

    if not rows:
        return {
            "message": "لا توجد بيانات كافية حتى الآن. أرسل أول إشارة من TradingView.",
            "avg_score": "-",
            "best_score_note": "-",
            "risk_note": "البيانات الآن محفوظة في Supabase ولن تضيع عند إعادة تشغيل Render."
        }

    scores = [r["score"] for r in rows if r.get("score") is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0

    return {
        "message": f"تم تحليل {len(rows)} إشارة محفوظة.",
        "avg_score": avg_score,
        "best_score_note": "هذه قراءة مبدئية. مرحلة WIN/LOSS تأتي بعد ربط متابعة السعر.",
        "risk_note": "البيانات محفوظة في Supabase PostgreSQL بشكل دائم."
    }


def learn_best_score():

    rows = fetch_recent(1000)

    closed = [
        r for r in rows
        if r.get("result") in ["WIN", "LOSS"]
    ]

    if len(closed) < 10:
        return {
            "status": "waiting",
            "message": "لا توجد صفقات مغلقة كافية للتعلم"
        }

    score_groups = {}

    for row in closed:

        score = row.get("score")

        if score is None:
            continue

        bucket = int(score / 10) * 10

        if bucket not in score_groups:
            score_groups[bucket] = {
                "wins": 0,
                "losses": 0
            }

        if row["result"] == "WIN":
            score_groups[bucket]["wins"] += 1
        else:
            score_groups[bucket]["losses"] += 1

    best_bucket = None
    best_rate = 0

    for bucket, stats in score_groups.items():

        total = stats["wins"] + stats["losses"]

        if total < 3:
            continue

        rate = (stats["wins"] / total) * 100

        if rate > best_rate:
            best_rate = rate
            best_bucket = bucket

    if best_bucket is not None:

        save_learning_insight(
            insight_key="best_score_range",
            insight_type="score",
            title=f"أفضل نطاق Score هو {best_bucket}-{best_bucket+9}",
            value=round(best_rate, 1),
            details={
                "score_range": f"{best_bucket}-{best_bucket+9}",
                "win_rate": round(best_rate, 1)
            }
        )

    return {
        "status": "success",
        "best_score_range": best_bucket,
        "win_rate": round(best_rate, 1)
    }


def learn_best_market_state():

    rows = fetch_recent(1000)

    closed = [
        r for r in rows
        if r.get("result") in ["WIN", "LOSS"]
    ]

    if len(closed) < 10:
        return {
            "status": "waiting",
            "message": "لا توجد صفقات مغلقة كافية"
        }

    states = {}

    for row in closed:

        state = row.get("market_state")

        if not state:
            continue

        if state not in states:
            states[state] = {
                "wins": 0,
                "losses": 0
            }

        if row["result"] == "WIN":
            states[state]["wins"] += 1
        else:
            states[state]["losses"] += 1

    best_state = None
    best_rate = 0

    for state, stats in states.items():

        total = stats["wins"] + stats["losses"]

        if total < 3:
            continue

        rate = (stats["wins"] / total) * 100

        if rate > best_rate:
            best_rate = rate
            best_state = state

    if best_state:

        save_learning_insight(
            insight_key="best_market_state",
            insight_type="market_state",
            title=f"أفضل حالة سوق هي {best_state}",
            value=round(best_rate, 1),
            details={
                "market_state": best_state,
                "win_rate": round(best_rate, 1)
            }
        )

    return {
        "status": "success",
        "best_market_state": best_state,
        "win_rate": round(best_rate, 1)
    }

def learn_best_timeframe():

    rows = fetch_recent(1000)

    closed = [
        r for r in rows
        if r.get("result") in ["WIN", "LOSS"]
    ]

    if len(closed) < 10:
        return {
            "status": "waiting",
            "message": "لا توجد صفقات مغلقة كافية"
        }

    timeframes = {}

    for row in closed:

        timeframe = row.get("timeframe")

        if not timeframe:
            continue

        if timeframe not in timeframes:
            timeframes[timeframe] = {
                "wins": 0,
                "losses": 0
            }

        if row["result"] == "WIN":
            timeframes[timeframe]["wins"] += 1
        else:
            timeframes[timeframe]["losses"] += 1

    best_timeframe = None
    best_rate = 0

    for timeframe, stats in timeframes.items():

        total = stats["wins"] + stats["losses"]

        if total < 3:
            continue

        rate = (stats["wins"] / total) * 100

        if rate > best_rate:
            best_rate = rate
            best_timeframe = timeframe

    if best_timeframe:

        save_learning_insight(
            insight_key="best_timeframe",
            insight_type="timeframe",
            title=f"أفضل فريم أداء هو {best_timeframe}",
            value=round(best_rate, 1),
            details={
                "timeframe": best_timeframe,
                "win_rate": round(best_rate, 1)
            }
        )

    return {
        "status": "success",
        "best_timeframe": best_timeframe,
        "win_rate": round(best_rate, 1)
    }


def learn_best_ticker():

    rows = fetch_recent(1000)

    closed = [
        r for r in rows
        if r.get("result") in ["WIN", "LOSS"]
    ]

    if len(closed) < 10:
        return {
            "status": "waiting",
            "message": "لا توجد صفقات مغلقة كافية"
        }

    tickers = {}

    for row in closed:

        ticker = row.get("ticker")

        if not ticker:
            continue

        if ticker not in tickers:
            tickers[ticker] = {
                "wins": 0,
                "losses": 0
            }

        if row["result"] == "WIN":
            tickers[ticker]["wins"] += 1
        else:
            tickers[ticker]["losses"] += 1

    best_ticker = None
    best_rate = 0

    for ticker, stats in tickers.items():

        total = stats["wins"] + stats["losses"]

        if total < 3:
            continue

        rate = (stats["wins"] / total) * 100

        if rate > best_rate:
            best_rate = rate
            best_ticker = ticker

    if best_ticker:

        save_learning_insight(
            insight_key="best_ticker",
            insight_type="ticker",
            title=f"أفضل أصل أداء هو {best_ticker}",
            value=round(best_rate, 1),
            details={
                "ticker": best_ticker,
                "win_rate": round(best_rate, 1)
            }
        )

    return {
        "status": "success",
        "best_ticker": best_ticker,
        "win_rate": round(best_rate, 1)
    }
