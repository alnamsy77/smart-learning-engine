from database import fetch_recent

def simple_learning_summary():
    """
    هذه نسخة V1 بسيطة.
    لاحقًا سنضيف مراقبة السعر بعد الإشارة ونحسب WIN / LOSS.
    الآن نعطي قراءة مبدئية من الإشارات المسجلة.
    """
    rows = fetch_recent(500)

    if not rows:
        return {
            "message": "لا توجد بيانات كافية حتى الآن. أرسل أول إشارة من TradingView.",
            "best_score_note": "-",
            "risk_note": "-"
        }

    scores = [r["score"] for r in rows if r["score"] is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0

    call_count = sum(1 for r in rows if r["signal"] == "CALL")
    put_count = sum(1 for r in rows if r["signal"] == "PUT")

    if avg_score >= 4.5:
        best_score_note = "جودة الإشارات الحالية قوية جدًا حسب Score."
    elif avg_score >= 4:
        best_score_note = "جودة الإشارات جيدة، لكن نحتاج نتائج WIN/LOSS للتأكيد."
    else:
        best_score_note = "الجودة متوسطة، نحتاج تشديد شروط الإشارة."

    risk_note = "لم يتم تفعيل تقييم WIN/LOSS بعد. هذه خطوة V2 بعد ربط مراقبة الأسعار."

    return {
        "message": f"تم تحليل {len(rows)} إشارة محفوظة.",
        "avg_score": avg_score,
        "call_count": call_count,
        "put_count": put_count,
        "best_score_note": best_score_note,
        "risk_note": risk_note
    }
