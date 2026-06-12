from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from database import init_db, insert_signal, fetch_recent, fetch_stats
from learning import simple_learning_summary

app = FastAPI(title="Smart Learning Engine Dashboard")


@app.on_event("startup")
def startup():
    init_db()


def pct(part, total):
    try:
        return round((part / total) * 100, 1) if total > 0 else 0
    except Exception:
        return 0


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
    win_count = stats.get("win_count", 0)
    loss_count = stats.get("loss_count", 0)

    target1_hit = stats.get("target1_hit", 0)
    target2_hit = stats.get("target2_hit", 0)
    target3_hit = stats.get("target3_hit", 0)

    closed_count = win_count + loss_count
    win_rate = pct(win_count, closed_count)

    target1_rate = pct(target1_hit, total)
    target2_rate = pct(target2_hit, total)
    target3_rate = pct(target3_hit, total)

    html_rows = ""
    for r in rows:
        signal = str(r.get("signal") or "").upper()
        result = str(r.get("result") or "OPEN").upper()
        status = str(r.get("status") or "OPEN").upper()

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

        status_ar = (
            "الهدف الأول 🎯" if status == "TARGET1_HIT"
            else "الهدف الثاني 🎯🎯" if status == "TARGET2_HIT"
            else "الهدف الثالث 🏆" if status == "TARGET3_HIT"
            else "خسارة ❌" if status == "LOSS"
            else "مفتوحة ⏳"
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
            <td>{r.get('target1') or ''}</td>
            <td>{r.get('target2') or ''}</td>
            <td>{r.get('target3') or ''}</td>
            <td>{status_ar}</td>
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
                background:
                    radial-gradient(circle at top right, rgba(249,115,22,0.16), transparent 30%),
                    radial-gradient(circle at bottom left, rgba(34,197,94,0.10), transparent 25%),
                    #020617;
                color:#e5e7eb;
                margin:0;
                padding:24px;
            }}
            .container {{
                max-width:1500px;
                margin:auto;
            }}
            h1 {{
                color:#f97316;
                margin-bottom:6px;
                font-size:34px;
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
                background:linear-gradient(90deg,#065f46,#047857);
                color:white;
                padding:8px 14px;
                border-radius:999px;
                font-size:13px;
                margin-bottom:12px;
                box-shadow:0 0 18px rgba(16,185,129,0.25);
            }}
            .quote {{
                background:linear-gradient(90deg,#111827,#1e293b);
                border:1px solid #374151;
                border-right:5px solid #f97316;
                border-radius:16px;
                padding:16px 18px;
                margin:18px 0;
                color:#fef3c7;
                font-size:16px;
                line-height:1.8;
            }}
            .quote b {{
                color:#f97316;
            }}
            .cards {{
                display:grid;
                grid-template-columns:repeat(5,1fr);
                gap:12px;
                margin-bottom:14px;
            }}
            .cards2 {{
                display:grid;
                grid-template-columns:repeat(3,1fr);
                gap:12px;
                margin-bottom:20px;
            }}
            .card {{
                background:linear-gradient(180deg,#111827,#0f172a);
                border:1px solid #374151;
                border-radius:16px;
                padding:16px;
                box-shadow:0 10px 25px rgba(0,0,0,0.28);
                position:relative;
                overflow:hidden;
            }}
            .card::after {{
                content:"";
                position:absolute;
                width:90px;
                height:90px;
                border-radius:50%;
                background:rgba(249,115,22,0.08);
                left:-25px;
                bottom:-25px;
            }}
            .card-title {{
                color:#9ca3af;
                font-size:13px;
            }}
            .num {{
                font-size:31px;
                font-weight:bold;
                margin-top:8px;
            }}
            .hint {{
                font-size:12px;
                color:#94a3b8;
                margin-top:6px;
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
            .target {{
                color:#38bdf8;
                font-weight:bold;
            }}
            .bar {{
                height:8px;
                background:#1f2937;
                border-radius:999px;
                margin-top:10px;
                overflow:hidden;
            }}
            .bar-fill {{
                height:100%;
                background:linear-gradient(90deg,#22c55e,#38bdf8);
                border-radius:999px;
            }}
            table {{
                width:100%;
                border-collapse:collapse;
                background:#111827;
                border-radius:16px;
                overflow:hidden;
                box-shadow:0 10px 25px rgba(0,0,0,0.30);
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
                position:sticky;
                top:0;
            }}
            tr:hover {{
                background:#1e293b;
            }}
            .footer-note {{
                margin-top:14px;
                color:#94a3b8;
                font-size:13px;
                text-align:center;
            }}
            @media (max-width: 1100px) {{
                .cards, .cards2 {{
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
            <div class="badge">النظام يعمل ✅ | استقبال الإشارات فعال ✅ | تتبع الأهداف مفعّل 🎯</div>
            <p class="subtitle">لوحة متابعة وتحليل إشارات الأسهم القادمة من TradingView.</p>

            <div class="quote">
                <b>قاعدة التداول:</b>
                لا تطارد السوق، ولا تدخل بلا خطة. الصبر على الفرصة أقوى من كثرة الدخول.
                الربح لا يأتي من كل إشارة، بل من الالتزام بالاستراتيجية وإدارة الصفقة حتى نهايتها.
            </div>

            <div class="cards">
                <div class="card">
                    <div class="card-title">إجمالي الإشارات</div>
                    <div class="num">{total}</div>
                    <div class="hint">كل الفرص المسجلة</div>
                </div>

                <div class="card">
                    <div class="card-title">إشارات صاعدة CALL</div>
                    <div class="num call">{call_count}</div>
                    <div class="hint">فرص اتجاه صاعد</div>
                </div>

                <div class="card">
                    <div class="card-title">إشارات هابطة PUT</div>
                    <div class="num put">{put_count}</div>
                    <div class="hint">فرص اتجاه هابط</div>
                </div>

                <div class="card">
                    <div class="card-title">صفقات مفتوحة</div>
                    <div class="num open">{open_count}</div>
                    <div class="hint">تحت المتابعة</div>
                </div>

                <div class="card">
                    <div class="card-title">نسبة النجاح</div>
                    <div class="num">{win_rate}%</div>
                    <div class="bar"><div class="bar-fill" style="width:{win_rate}%"></div></div>
                </div>
            </div>

            <div class="cards2">
                <div class="card">
                    <div class="card-title">🎯 تحقق الهدف الأول</div>
                    <div class="num target">{target1_hit}</div>
                    <div class="hint">{target1_rate}% من إجمالي الإشارات</div>
                    <div class="bar"><div class="bar-fill" style="width:{target1_rate}%"></div></div>
                </div>

                <div class="card">
                    <div class="card-title">🎯 تحقق الهدف الثاني</div>
                    <div class="num target">{target2_hit}</div>
                    <div class="hint">{target2_rate}% من إجمالي الإشارات</div>
                    <div class="bar"><div class="bar-fill" style="width:{target2_rate}%"></div></div>
                </div>

                <div class="card">
                    <div class="card-title">🏆 تحقق الهدف الثالث</div>
                    <div class="num target">{target3_hit}</div>
                    <div class="hint">{target3_rate}% من إجمالي الإشارات</div>
                    <div class="bar"><div class="bar-fill" style="width:{target3_rate}%"></div></div>
                </div>
            </div>

            <div class="cards2">
                <div class="card">
                    <div class="card-title">صفقات رابحة</div>
                    <div class="num win">{win_count}</div>
                    <div class="hint">وصلت هدفًا واحدًا على الأقل</div>
                </div>

                <div class="card">
                    <div class="card-title">صفقات خاسرة</div>
                    <div class="num loss">{loss_count}</div>
                    <div class="hint">هبوط 3% من سعر الدخول</div>
                </div>

                <div class="card">
                    <div class="card-title">الصفقات المغلقة</div>
                    <div class="num">{closed_count}</div>
                    <div class="hint">رابحة + خاسرة</div>
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
                        <th>الجودة</th>
                        <th>ATR%</th>
                        <th>هدف 1</th>
                        <th>هدف 2</th>
                        <th>هدف 3</th>
                        <th>الحالة</th>
                        <th>النتيجة</th>
                    </tr>
                </thead>
                <tbody>
                    {html_rows}
                </tbody>
            </table>

            <div class="footer-note">
                هذه اللوحة للتعلّم والتحليل وليست توصية شراء أو بيع. القرار النهائي يكون وفق خطتك وإدارتك للمخاطر.
            </div>
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
