from database import fetch_recent, save_learning_insight


MIN_CLOSED_TRADES = 10
MIN_GROUP_TRADES = 3


def _closed_rows(limit=1000):
    rows = fetch_recent(limit)
    return [r for r in rows if r.get("result") in ["WIN", "LOSS"]]


def _win_rate(wins, losses):
    total = wins + losses
    return round((wins / total) * 100, 1) if total > 0 else 0


def _learn_best_group(column, insight_key, insight_type, title_prefix):
    closed = _closed_rows(1000)

    if len(closed) < MIN_CLOSED_TRADES:
        return {
            "status": "waiting",
            "message": "لا توجد صفقات مغلقة كافية للتعلم"
        }

    groups = {}

    for row in closed:
        value = row.get(column)

        if value is None or value == "":
            continue

        value = str(value)

        if value not in groups:
            groups[value] = {"wins": 0, "losses": 0}

        if row.get("result") == "WIN":
            groups[value]["wins"] += 1
        elif row.get("result") == "LOSS":
            groups[value]["losses"] += 1

    best_value = None
    best_rate = 0
    best_total = 0

    for value, stats in groups.items():
        total = stats["wins"] + stats["losses"]

        if total < MIN_GROUP_TRADES:
            continue

        rate = _win_rate(stats["wins"], stats["losses"])

        if rate > best_rate:
            best_rate = rate
            best_value = value
            best_total = total

    if best_value is not None:
        save_learning_insight(
            insight_key=insight_key,
            insight_type=insight_type,
            title=f"{title_prefix}: {best_value}",
            value=best_rate,
            details={
                "column": column,
                "best_value": best_value,
                "win_rate": best_rate,
                "total": best_total
            }
        )

    return {
        "status": "success",
        "best_value": best_value,
        "win_rate": best_rate,
        "total": best_total
    }


def simple_learning_summary():
    rows = fetch_recent(500)

    if not rows:
        return {
            "message": "لا توجد بيانات كافية حتى الآن.",
            "avg_score": "-",
            "best_score_note": "-",
            "risk_note": "البيانات محفوظة في Supabase PostgreSQL."
        }

    scores = [r["score"] for r in rows if r.get("score") is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0

    return {
        "message": f"تم تحليل {len(rows)} إشارة محفوظة.",
        "avg_score": avg_score,
        "best_score_note": "التعلم يعتمد على الصفقات المغلقة WIN/LOSS.",
        "risk_note": "الإعدادات تحفظ الآن مع كل صفقة."
    }


def learn_best_score():
    return _learn_best_group(
        column="score",
        insight_key="best_score",
        insight_type="score",
        title_prefix="أفضل درجة جودة"
    )


def learn_best_market_state():
    return _learn_best_group(
        column="market_state",
        insight_key="best_market_state",
        insight_type="market_state",
        title_prefix="أفضل حالة سوق"
    )


def learn_best_timeframe():
    return _learn_best_group(
        column="timeframe",
        insight_key="best_timeframe",
        insight_type="timeframe",
        title_prefix="أفضل فريم"
    )


def learn_best_ticker():
    return _learn_best_group(
        column="ticker",
        insight_key="best_ticker",
        insight_type="ticker",
        title_prefix="أفضل سهم / عملة"
    )


def learn_best_atr_range():
    closed = _closed_rows(1000)

    if len(closed) < MIN_CLOSED_TRADES:
        return {
            "status": "waiting",
            "message": "لا توجد صفقات مغلقة كافية"
        }

    groups = {}

    for row in closed:
        atr_pct = row.get("atr_pct")

        if atr_pct is None:
            continue

        bucket = int(float(atr_pct))
        bucket_name = f"{bucket}-{bucket + 1}%"

        if bucket_name not in groups:
            groups[bucket_name] = {"wins": 0, "losses": 0}

        if row.get("result") == "WIN":
            groups[bucket_name]["wins"] += 1
        elif row.get("result") == "LOSS":
            groups[bucket_name]["losses"] += 1

    best_bucket = None
    best_rate = 0
    best_total = 0

    for bucket, stats in groups.items():
        total = stats["wins"] + stats["losses"]

        if total < MIN_GROUP_TRADES:
            continue

        rate = _win_rate(stats["wins"], stats["losses"])

        if rate > best_rate:
            best_rate = rate
            best_bucket = bucket
            best_total = total

    if best_bucket:
        save_learning_insight(
            insight_key="best_atr_range",
            insight_type="atr_pct",
            title=f"أفضل نطاق ATR%: {best_bucket}",
            value=best_rate,
            details={
                "atr_range": best_bucket,
                "win_rate": best_rate,
                "total": best_total
            }
        )

    return {
        "status": "success",
        "best_atr_range": best_bucket,
        "win_rate": best_rate,
        "total": best_total
    }


def learn_best_pivot_left():
    return _learn_best_group("pivot_left", "best_pivot_left", "pivot_left", "أفضل Pivot Left")


def learn_best_pivot_right():
    return _learn_best_group("pivot_right", "best_pivot_right", "pivot_right", "أفضل Pivot Right")


def learn_best_cooldown_bars():
    return _learn_best_group("cooldown_bars", "best_cooldown_bars", "cooldown_bars", "أفضل Cooldown")


def learn_best_min_score():
    return _learn_best_group("min_score", "best_min_score", "min_score", "أفضل Min Score")


def learn_best_rf_period():
    return _learn_best_group("rf_period", "best_rf_period", "rf_period", "أفضل RF Period")


def learn_best_rf_multiplier():
    return _learn_best_group("rf_multiplier", "best_rf_multiplier", "rf_multiplier", "أفضل RF Multiplier")


def learn_best_rqk_len():
    return _learn_best_group("rqk_len", "best_rqk_len", "rqk_len", "أفضل RQK Length")


def learn_best_rqk_weight():
    return _learn_best_group("rqk_weight", "best_rqk_weight", "rqk_weight", "أفضل RQK Weight")


def learn_best_atr_len():
    return _learn_best_group("atr_len", "best_atr_len", "atr_len", "أفضل ATR Length")


def learn_best_min_atr_pct():
    return _learn_best_group("min_atr_pct", "best_min_atr_pct", "min_atr_pct", "أفضل Min ATR%")


def learn_best_target_mult_1():
    return _learn_best_group("target_mult_1", "best_target_mult_1", "target_mult_1", "أفضل هدف 1")


def learn_all_settings():
    return {
        "best_score": learn_best_score(),
        "best_market_state": learn_best_market_state(),
        "best_timeframe": learn_best_timeframe(),
        "best_ticker": learn_best_ticker(),
        "best_atr_range": learn_best_atr_range(),

        "best_pivot_left": learn_best_pivot_left(),
        "best_pivot_right": learn_best_pivot_right(),
        "best_cooldown_bars": learn_best_cooldown_bars(),
        "best_min_score": learn_best_min_score(),
        "best_rf_period": learn_best_rf_period(),
        "best_rf_multiplier": learn_best_rf_multiplier(),
        "best_rqk_len": learn_best_rqk_len(),
        "best_rqk_weight": learn_best_rqk_weight(),
        "best_atr_len": learn_best_atr_len(),
        "best_min_atr_pct": learn_best_min_atr_pct(),
        "best_target_mult_1": learn_best_target_mult_1()
    }


def generate_ai_recommendation():
    learning = learn_all_settings()

    def pick(key, label):
        item = learning.get(key, {})
        value = item.get("best_value")
        win_rate = item.get("win_rate", 0)
        total = item.get("total", 0)

        if value is None or total == 0:
            return {
                "label": label,
                "value": None,
                "win_rate": win_rate,
                "total": total,
                "note": "لا توجد بيانات كافية"
            }

        return {
            "label": label,
            "value": value,
            "win_rate": win_rate,
            "total": total,
            "note": f"نسبة النجاح {win_rate}% من {total} صفقات مغلقة"
        }

    recommendation = {
        "status": "success",
        "message": "توصية مبدئية مبنية على الصفقات المغلقة فقط. لا تعتمد عليها إلا بعد تراكم بيانات كافية.",
        "minimum_data_rule": {
            "min_closed_trades": MIN_CLOSED_TRADES,
            "min_group_trades": MIN_GROUP_TRADES
        },
        "recommended_settings": {
            "score": pick("best_score", "أفضل درجة جودة"),
            "market_state": pick("best_market_state", "أفضل حالة سوق"),
            "timeframe": pick("best_timeframe", "أفضل فريم"),
            "ticker": pick("best_ticker", "أفضل سهم / عملة"),
            "atr_range": {
                "label": "أفضل نطاق ATR%",
                "value": learning.get("best_atr_range", {}).get("best_atr_range"),
                "win_rate": learning.get("best_atr_range", {}).get("win_rate", 0),
                "total": learning.get("best_atr_range", {}).get("total", 0)
            },
            "pivot_left": pick("best_pivot_left", "Pivot Left"),
            "pivot_right": pick("best_pivot_right", "Pivot Right"),
            "cooldown_bars": pick("best_cooldown_bars", "Cooldown Bars"),
            "min_score": pick("best_min_score", "Min Score"),
            "rf_period": pick("best_rf_period", "RF Period"),
            "rf_multiplier": pick("best_rf_multiplier", "RF Multiplier"),
            "rqk_len": pick("best_rqk_len", "RQK Length"),
            "rqk_weight": pick("best_rqk_weight", "RQK Weight"),
            "atr_len": pick("best_atr_len", "ATR Length"),
            "min_atr_pct": pick("best_min_atr_pct", "Min ATR%"),
            "target_mult_1": pick("best_target_mult_1", "Target 1 Multiplier")
        }
    }

    save_learning_insight(
        insight_key="ai_recommendation",
        insight_type="ai_recommendation",
        title="توصية الذكاء الاصطناعي للإعدادات",
        value=0,
        details=recommendation
    )

    return recommendation
