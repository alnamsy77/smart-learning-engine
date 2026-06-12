from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from database import init_db, insert_signal, fetch_recent, fetch_stats
from learning import simple_learning_summary

app = FastAPI(title="Smart Learning Engine V1.1")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def dashboard():
    try:
        stats = fetch_stats()
        rows = fetch_recent(50)
        learning = simple_learning_summary()
    except Exception as e:
        return f"""
        <html lang="ar" dir="rtl">
        <body style="font-family:Arial;background:#111827;color:white;padding:30px">
        <h1>Smart Learning Engine V1.1</h1>
        <h2 style="color:#ef4444">خطأ في الاتصال بقاعدة البيانات</h2>
        <pre style="white-space:pre-wrap;background:#1f2937;padding:15px;border-radius:8px">{str(e)}</pre>
        </body>
        </html>
        """

    html_rows = ""
    for r in rows:
        signal_class = "call" if r.get("signal") == "CALL" else "put" if r.get("signal") == "PUT" else ""
        html_rows += f"""
        <tr>
            <td>{r.get('id')}</td>
            <td>{r.get('created_at')}</td>
            <td><b>{r.get('ticker') or ''}</b></td>
            <td class="{signal_class}">{r.get('signal') or ''}</td>
            <td>{r.get('timeframe') or ''}</td>
            <td>{r.get('price') or ''}</td>
            <td>{r.get('score') or ''}/5</td>
            <td>{r.get('atr_pct') or ''}%</td>
            <td>{r.get('market_state') or ''}</td>
            <td>{r.get('result') or ''}</td>
        </tr>
        """

    return f"""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>Smart Learning Engine V1.1</title>
        <style>
            body {{font-family: Arial, sans-serif;background:#0f172a;color:#e5e7eb;margin:0;padding:24px;}}
            .container {{max-width:1200px;margin:auto;}}
            h1 {{color:#f97316;}}
            .badge {{display:inline-block;background:#065f46;color:white;padding:6px 10px;border-radius:999px;font-size:13px;margin-bottom:12px;}}
            .cards {{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px;}}
            .card {{background:#111827;border:1px solid #374151;border-radius:12px;padding:16px;}}
            .num {{font-size:28px;font-weight:bold;margin-top:8px;}}
            .learning {{background:#172554;border:1px solid #2563eb;border-radius:12px;padding:16px;margin-bottom:18px;}}
            table {{width:100%;border-collapse:collapse;background:#111827;border-radius:12px;overflow:hidden;}}
            th, td {{border-bottom:1px solid #374151;padding:10px;text-align:center;font-size:14px;}}
            th {{background:#1f2937;}}
            .call {{color:#22c55e;font-weight:bold;}}
            .put {{color:#ef4444;font-weight:bold;}}
            .small {{color:#9ca3af;font-size:13px;}}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠🔥 Smart Learning Engine V1.1</h1>
            <div class="badge">Supabase PostgreSQL دائم ✅ | Webhook Active ✅ | Signals Saved ✅</div>
            <p class="small">لوحة استقبال وتحليل إشارات TradingView.</p>

            <div class="cards">
                <div class="card">إجمالي الإشارات<div class="num">{stats['total']}</div></div>
                <div class="card">CALL<div class="num call">{stats['call_count']}</div></div>
                <div class="card">PUT<div class="num put">{stats['put_count']}</div></div>
                <div class="card">OPEN<div class="num">{stats['open_count']}</div></div>
            </div>

            <div class="learning">
                <h2>🧠 قراءة التعلم المبدئية</h2>
                <p>{learning.get('message')}</p>
                <p>متوسط الجودة: <b>{learning.get('avg_score', '-')}</b></p>
                <p>{learning.get('best_score_note')}</p>
                <p>{learning.get('risk_note')}</p>
                <p>✅ تم استقبال وحفظ الإشارات بنجاح. مرحلة WIN/LOSS هي المرحلة القادمة بعد ربط متابعة السعر.</p>
            </div>

            <h2>آخر الإشارات</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>الوقت</th>
                        <th>السهم</th>
                        <th>الإشارة</th>
                        <th>الفريم</th>
                        <th>السعر</th>
                        <th>Score</th>
                        <th>ATR%</th>
                        <th>حالة السوق</th>
                        <th>النتيجة</th>
                    </tr>
                </thead>
                <tbody>
                    {html_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """


@app.post("/webhook/tradingview")
async def tradingview_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        raw = await request.body()
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": "Invalid JSON",
                "raw": raw.decode("utf-8", errors="ignore")
            }
        )

    try:
        inserted_id = insert_signal(data)
        return {
            "ok": True,
            "message": "Signal saved permanently in Supabase",
            "id": inserted_id
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )


@app.get("/api/signals")
def api_signals():
    return fetch_recent(100)


@app.get("/api/stats")
def api_stats():
    stats = fetch_stats()
    stats["learning"] = simple_learning_summary()
    return stats
