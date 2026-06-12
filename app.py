from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from database import init_db, insert_signal, fetch_recent, fetch_stats
from learning import simple_learning_summary

app = FastAPI(title="Smart Learning Engine Dashboard")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def dashboard():
    try:
        stats = fetch_stats()
        rows = fetch_recent(100)
    except Exception as e:
        return f"""
        <html lang="ar" dir="rtl">
        <body style="font-family:Arial;background:#111827;color:white;padding:30px">
        <h1>لوحة محرك التعلم الذكي</h1>
        <h2 style="color:#ef4444">خطأ في الاتصال بقاعدة البيانات</h2>
        <pre style="white-space:pre-wrap;background:#1f2937;padding:15px;border-radius:8px">{str(e)}</pre>
        </body>
        </html>
        """

    total = stats.get("total", 0)
    call_count = stats.get("call_count", 0)
    put_count = stats.get("put_count", 0)
    open_count = stats.get("open_count", 0)

    win_count = 0
    loss_count = 0

    for r in rows:
        result = str(r.get("result") or "").upper()
        if result == "WIN":
            win_count += 1
        elif result == "LOSS":
            loss_count += 1

    closed_count = win_count + loss_count
    win_rate = round((win_count / closed_count) * 100, 2) if closed_count > 0 else 0

    html_rows = ""
    for r in rows:
        signal = str(r.get("signal") or "").upper()
        result = str(r.get("result") or "OPEN").upper()

        signal_class = "call" if signal == "CALL" else "put" if signal == "PUT" else ""
        result_class = (
            "win" if result == "WIN"
            else "loss" if result == "LOSS"
            else "open"
        )

        result_ar = (
            "رابحة ✅" if result == "WIN"
            else "خاسرة ❌" if result == "LOSS"
            else "مفتوحة ⏳"
        )

        signal_ar = (
            "صاعدة CALL" if signal == "CALL"
            else "هابطة PUT" if signal == "PUT"
            else signal
        )

        html_rows += f"""
        <tr>
            <td>{r.get('id')}</td>
            <td>{r.get('created_at') or ''}</td>
            <td><b>{r.get('ticker') or ''}</b></td>
            <td class="{signal_class}">{signal_ar}</td>
            <td>{r.get('timeframe') or ''}</td>
            <td>{r.get('price') or ''}</td>
            <td>{r.get('score') or ''}/5</td>
            <td>{r.get('atr_pct') or ''}%</td>
            <td>{r.get('market_state') or ''}</td>
            <td class="{result_class}">{result_ar}</td>
        </tr>
        """

    return f"""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>لوحة محرك التعلم الذكي</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background:#020617;
                color:#e5e7eb;
                margin:0;
                padding:24px;
            }}
            .container {{
                max-width:1350px;
                margin:auto;
            }}
            h1 {{
                color:#f97316;
                margin-bottom:6px;
            }}
            h2 {{
                color:#f9fafb;
                margin-top:24px;
            }}
            .subtitle {{
                color:#9ca3af;
                margin-bottom:18px;
            }}
            .badge {{
                display:inline-block;
                background:#065f46;
                color:white;
                padding:7px 12px;
                border-radius:999px;
                font-size:13px;
                margin-bottom:12px;
            }}
            .cards {{
                display:grid;
                grid-template-columns:repeat(6,1fr);
                gap:12px;
                margin-bottom:18px;
            }}
            .card {{
                background:#111827;
                border:1px solid #374151;
                border-radius:14px;
                padding:16px;
                box-shadow:0 10px 25px rgba(0,0,0,0.25);
            }}
            .card-title {{
                color:#9ca3af;
                font-size:13px;
            }}
            .num {{
                font-size:30px;
                font-weight:bold;
                margin-top:8px;
            }}
            .learning {{
                background:#172554;
                border:1px solid #2563eb;
                border-radius:14px;
                padding:18px;
                margin-bottom:18px;
            }}
            table {{
                width:100%;
                border-collapse:collapse;
                background:#111827;
                border-radius:14px;
                overflow:hidden;
            }}
            th, td {{
                border-bottom:1px solid #374151;
                padding:11px;
                text-align:center;
                font-size:14px;
            }}
            th {{
                background:#1f2937;
                color:#f9fafb;
            }}
            tr:hover {{
                background:#1e293b;
            }}
            .call {{
                color:#22c55e;
                font-weight:bold;
            }}
            .put {{
                color:#ef4444;
                font-weight:bold;
            }}
            .win {{
                color:#22c55e;
                font-weight:bold;
            }}
            .loss {{
                color:#ef4444;
                font-weight:bold;
            }}
            .open {{
                color:#facc15;
                font-weight:bold;
            }}
            .small {{
                color:#9ca3af;
                font-size:13px;
            }}
            @media (max-width: 1000px) {{
                .cards {{
                    grid-template-columns:repeat(2,1fr);
                }}
                table {{
                    font-size:12px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠🔥 لوحة محرك التعلم الذكي</h1>
            <div class="badge">Supabase ✅ | Webhook ✅ | TradingView Signals ✅</div>
            <p class="subtitle">لوحة متابعة وتحليل إشارات الأسهم القادمة من TradingView.</p>

            <div class="cards">
                <div class="card">
                    <div class="card-title">إجمالي الإشارات</div>
                    <div class="num">{total}</div>
                </div>

                <div class="card">
                    <div class="card-title">إشارات صاعدة CALL</div>
                    <div class="num call">{call_count}</div>
                </div>

                <div class="card">
                    <div class="card-title">إشارات هابطة PUT</div>
                    <div class="num put">{put_count}</div>
                </div>

                <div class="card">
                    <div class="card-title">صفقات مفتوحة</div>
                    <div class="num open">{open_count}</div>
                </div>

                <div class="card">
                    <div class="card-title">صفقات رابحة</div>
                    <div class="num win">{win_count}</div>
                </div>

                <div class="card">
                    <div class="card-title">نسبة النجاح</div>
                    <div class="num">{win_rate}%</div>
                </div>
            </div>

            <h2>📋 آخر الإشارات</h2>
            <table>
                <thead>
                    <tr>
                        <th>الرقم</th>
                        <th>وقت الإشارة</th>
                        <th>السهم</th>
                        <th>نوع الإشارة</th>
                        <th>الفريم</th>
                        <th>سعر الدخول</th>
                        <th>درجة الجودة</th>
                        <th>نسبة ATR</th>
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
