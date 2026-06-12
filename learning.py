from database import fetch_recent

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
