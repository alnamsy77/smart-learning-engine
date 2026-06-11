from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from database import init_db, insert_signal, fetch_recent, fetch_stats
from learning import simple_learning_summary

app = FastAPI(title="Smart Learning Engine V1")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def dashboard():
    stats = fetch_stats()
    rows = fetch_recent(50)
    learning = simple_learning_summary()

    html_rows = ""
    for r in rows:
        signal_class = "call" if r["signal"] == "CALL" else "put" if r["signal"] == "PUT" else ""
        html_rows += f"""
        <tr>
            <td>{r['id']}</td>
            <td>{r['created_at']}</td>
            <td><b>{r['ticker'] or ''}</b></td>
            <td class="{signal_class}">{r['signal'] or ''}</td>
            <td>{r['timeframe'] or ''}</td>
            <td>{r['price'] or ''}</td>
            <td>{r['score'] or ''}/5</td>
            <td>{r['atr_pct'] or ''}%</td>
            <td>{r['market_state'] or ''}</td>
            <td>{r['result'] or ''}</td>
        </tr>
        """

    html = f"""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>Smart Learning Engine V1</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: #e5e7eb;
                margin: 0;
                padding: 24px;
            }}
            .container {{ max-width: 1200px; margin: auto; }}
            h1 {{ color: #f97316; }}
            .cards {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 12px;
                margin-bottom: 18px;
            }}
            .card {{
                background: #111827;
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 16px;
            }}
            .num {{ font-size: 28px; font-weight: bold; margin-top: 8px; }}
            .learning {{
                background: #172554;
                border: 1px solid #2563eb;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 18px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: #111827;
                border-radius: 12px;
                overflow: hidden;
            }}
            th, td {{
                border-bottom: 1px solid #374151;
                padding: 10px;
                text-align: center;
                font-size: 14px;
            }}
            th {{ background: #1f2937; }}
            .call {{ color: #22c55e; font-weight: bold; }}
            .put {{ color: #ef4444; font-weight: bold; }}
            .small {{ color: #9ca3af; font-size: 13px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠🔥 Smart Learning Engine V1</h1>
            <p class="small">لوحة استقبال وتحليل إشارات TradingView لصائد الترند.</p>

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
    return html

@app.post("/webhook/tradingview")
async def tradingview_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        raw = await request.body()
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Invalid JSON", "raw": raw.decode("utf-8", errors="ignore")}
        )

    inserted_id = insert_signal(data)
    return {"ok": True, "message": "Signal saved", "id": inserted_id}

@app.get("/api/signals")
def api_signals():
    rows = fetch_recent(100)
    return [dict(r) for r in rows]

@app.get("/api/stats")
def api_stats():
    stats = fetch_stats()
    stats["by_ticker"] = [dict(r) for r in stats["by_ticker"]]
    stats["by_market"] = [dict(r) for r in stats["by_market"]]
    stats["learning"] = simple_learning_summary()
    return stats
