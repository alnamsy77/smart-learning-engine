from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from database import (
    init_db,
    insert_signal,
    fetch_recent,
    fetch_stats,
    get_learning_insights
)
from learning import (
    simple_learning_summary,
    learn_best_score,
    learn_best_market_state,
    learn_best_timeframe,
    learn_best_ticker
)


import os
import secrets

app = FastAPI(title="Smart Learning Engine Dashboard")

# =========================
# Admin Login Settings
# =========================

ADMIN_USER = os.getenv("ADMIN_USER", "owner")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456")

SESSION_TOKEN = secrets.token_urlsafe(32)

# =========================
# Startup
# =========================

@app.on_event("startup")
def startup():
    init_db()

# =========================
# Login Helpers
# =========================

def is_logged_in(request: Request):
    return request.cookies.get("admin_session") == SESSION_TOKEN


@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <html dir="rtl">
    <head>
        <title>تسجيل دخول المالك</title>
        <style>
            body{
                background:#020617;
                color:white;
                font-family:Arial;
                display:flex;
                justify-content:center;
                align-items:center;
                height:100vh;
            }
            .box{
                background:#111827;
                padding:30px;
                border-radius:15px;
                width:350px;
            }
            input{
                width:100%;
                padding:10px;
                margin-top:10px;
                margin-bottom:15px;
            }
            button{
                width:100%;
                padding:10px;
                background:#f97316;
                border:none;
                color:white;
                cursor:pointer;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>🔐 دخول لوحة المالك</h2>
            <form method="post" action="/login">
                <input name="username" placeholder="اسم المستخدم">
                <input name="password" type="password" placeholder="كلمة المرور">
                <button type="submit">دخول</button>
            </form>
        </div>
    </body>
    </html>
    """


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        response = RedirectResponse("/admin", status_code=302)
        response.set_cookie(
            key="admin_session",
            value=SESSION_TOKEN,
            httponly=True
        )
        return response

    return RedirectResponse("/login", status_code=302)

def pct(part, total):
    try:
        return round((part / total) * 100, 1) if total > 0 else 0
    except Exception:
        return 0


def ar_signal(value):
    v = str(value or "").upper()
    if v == "CALL":
        return "فرصة صاعدة 🟢"
    if v == "PUT":
        return "فرصة هابطة 🔴"
    return v or "-"


def ar_status(value):
    v = str(value or "OPEN").upper()
    if v == "TARGET1_HIT":
        return "تحقق الهدف الأول 🎯"
    if v == "TARGET2_HIT":
        return "تحقق الهدف الثاني 🎯🎯"
    if v == "TARGET3_HIT":
        return "تحقق الهدف الثالث 🏆"
    if v == "LOSS":
        return "صفقة خاسرة ❌"
    return "تحت المتابعة ⏳"


def ar_result(value):
    v = str(value or "OPEN").upper()
    if v == "WIN":
        return "رابحة ✅"
    if v == "LOSS":
        return "خاسرة ❌"
    return "مفتوحة ⏳"


def ar_market(value):
    v = str(value or "").upper()
    if v == "BULL_TREND":
        return "ترند صاعد 📈"
    if v == "BEAR_TREND":
        return "ترند هابط 📉"
    if v == "SIDEWAYS":
        return "سوق عرضي ↔️"
    if v == "MIXED":
        return "سوق متذبذب ⚖️"
    if not v:
        return "-"
    return v


def ar_score(value):
    if value in [None, "", "-"]:
        return "-"
    return f"{value} من 5"


def group_name(group):
    if not group:
        return "-"
    name = group.get("name", "-")
    return "-" if name is None else str(name)


def group_rate(group):
    if not group:
        return 0
    return group.get("win_rate", 0) or 0


def group_total(group):
    if not group:
        return 0
    return group.get("total", 0) or 0


# =========================
# Admin Dashboard
# =========================

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):

    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=302)

    insights = get_learning_insights()

    insight_map = {
        item.get("insight_key"): item
        for item in insights
    }

    best_score = insight_map.get("best_score_range", {})
    best_market = insight_map.get("best_market_state", {})
    best_timeframe = insight_map.get("best_timeframe", {})
    best_ticker = insight_map.get("best_ticker", {})

    best_score_title = best_score.get("title", "لا توجد بيانات بعد")
    best_score_value = best_score.get("value", "-")

    best_market_title = best_market.get("title", "لا توجد بيانات بعد")
    best_market_value = best_market.get("value", "-")

    best_timeframe_title = best_timeframe.get("title", "لا توجد بيانات بعد")
    best_timeframe_value = best_timeframe.get("value", "-")

    best_ticker_title = best_ticker.get("title", "لا توجد بيانات بعد")
    best_ticker_value = best_ticker.get("value", "-")

    
    return f"""
    <html dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>لوحة المالك</title>

        <style>
            body{
                background:#020617;
                color:white;
                font-family:Arial;
                padding:40px;
            }

            .card{
                background:#111827;
                border:1px solid #374151;
                border-radius:16px;
                padding:20px;
                margin-bottom:20px;
            }

            h1{
                color:#f97316;
            }

            h2{
                color:#38bdf8;
            }

            ul{
                line-height:2;
            }
        </style>
    </head>

    <body>

        <h1>🔐 لوحة المالك الخاصة</h1>

        <div class="card">
            <h2>🧠 محرك التعلم الذكي</h2>

           <ul>
    <li>{best_score_title} — نسبة النجاح: {best_score_value}%</li>
    <li>{best_market_title} — نسبة النجاح: {best_market_value}%</li>
    <li>{best_timeframe_title} — نسبة النجاح: {best_timeframe_value}%</li>
    <li>{best_ticker_title} — نسبة النجاح: {best_ticker_value}%</li>
</ul>
        </div>

        <div class="card">
            <h2>🚧 قيد التطوير</h2>

            <p>
            هذه الصفحة مخصصة لك فقط وسوف نضيف فيها
            جميع تحليلات الذكاء الاصطناعي الخاصة بالمؤشر.
            </p>
        </div>

    </body>
    </html>
    """

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

    call_win_rate = stats.get("call_win_rate", 0)
    put_win_rate = stats.get("put_win_rate", 0)

    best_score = stats.get("best_score", {})
    best_market_state = stats.get("best_market_state", {})
    best_timeframe = stats.get("best_timeframe", {})
    best_ticker = stats.get("best_ticker", {})

    closed_count = win_count + loss_count
    win_rate = pct(win_count, closed_count)
    loss_rate = pct(loss_count, closed_count)

    target1_rate = pct(target1_hit, total)
    target2_rate = pct(target2_hit, total)
    target3_rate = pct(target3_hit, total)

    best_score_name = group_name(best_score)
    best_market_name = ar_market(group_name(best_market_state))
    best_timeframe_name = group_name(best_timeframe)
    best_ticker_name = group_name(best_ticker)

    html_rows = ""
    for r in rows:
        signal = str(r.get("signal") or "").upper()
        result = str(r.get("result") or "OPEN").upper()

        signal_class = "call" if signal == "CALL" else "put" if signal == "PUT" else ""
        result_class = "win" if result == "WIN" else "loss" if result == "LOSS" else "open"

        html_rows += f"""
        <tr>
            <td>{r.get('id')}</td>
            <td>{r.get('created_at') or ''}</td>
            <td><b>{r.get('ticker') or ''}</b></td>
            <td class="{signal_class}">{ar_signal(r.get('signal'))}</td>
            <td>{r.get('timeframe') or ''}</td>
            <td>{r.get('price') or ''}</td>
            <td>{ar_score(r.get('score'))}</td>
            <td>{r.get('atr_pct') or ''}%</td>
            <td>{r.get('target1') or ''}</td>
            <td>{r.get('target2') or ''}</td>
            <td>{r.get('target3') or ''}</td>
            <td>{ar_market(r.get('market_state'))}</td>
            <td>{ar_status(r.get('status'))}</td>
            <td class="{result_class}">{ar_result(r.get('result'))}</td>
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
                    radial-gradient(circle at top right, rgba(249,115,22,0.18), transparent 30%),
                    radial-gradient(circle at bottom left, rgba(34,197,94,0.12), transparent 25%),
                    #020617;
                color:#e5e7eb;
                margin:0;
                padding:24px;
            }}
            .container {{
                max-width:1550px;
                margin:auto;
            }}
            h1 {{
                color:#f97316;
                margin-bottom:6px;
                font-size:34px;
            }}
            h2 {{
                color:#f9fafb;
                margin-top:26px;
                margin-bottom:14px;
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
            .cards4 {{
                display:grid;
                grid-template-columns:repeat(4,1fr);
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
            .big-text {{
                font-size:23px;
                font-weight:bold;
                margin-top:8px;
                color:#f9fafb;
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
            .gold {{
                color:#facc15;
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
            .bar-fill-red {{
                height:100%;
                background:linear-gradient(90deg,#ef4444,#f97316);
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
                .cards, .cards2, .cards4 {{
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
            <p class="subtitle">لوحة عربية لمتابعة أداء المؤشر والإشارات القادمة من TradingView.</p>

            <div class="quote">
                <b>قاعدة التداول:</b>
                لا تطارد السوق، ولا تدخل بلا خطة. الصبر على الفرصة أقوى من كثرة الدخول.
                الربح لا يأتي من كل إشارة، بل من الالتزام بالاستراتيجية وإدارة الصفقة حتى نهايتها.
            </div>

            <h2>📊 أداء المؤشر العام</h2>
            <div class="cards">
                <div class="card">
                    <div class="card-title">إجمالي إشارات المؤشر</div>
                    <div class="num">{total}</div>
                    <div class="hint">كل الفرص المسجلة</div>
                </div>

                <div class="card">
                    <div class="card-title">نسبة نجاح المؤشر</div>
                    <div class="num win">{win_rate}%</div>
                    <div class="bar"><div class="bar-fill" style="width:{win_rate}%"></div></div>
                </div>

                <div class="card">
                    <div class="card-title">نسبة الخسارة</div>
                    <div class="num loss">{loss_rate}%</div>
                    <div class="bar"><div class="bar-fill-red" style="width:{loss_rate}%"></div></div>
                </div>

                <div class="card">
                    <div class="card-title">صفقات مفتوحة</div>
                    <div class="num open">{open_count}</div>
                    <div class="hint">تحت المتابعة</div>
                </div>

                <div class="card">
                    <div class="card-title">صفقات مغلقة</div>
                    <div class="num">{closed_count}</div>
                    <div class="hint">رابحة + خاسرة</div>
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

            <h2>🧭 قراءة ظروف السوق وأداء الفرص</h2>
            <div class="cards4">
                <div class="card">
                    <div class="card-title">🟢 نجاح الفرص الصاعدة</div>
                    <div class="num call">{call_win_rate}%</div>
                    <div class="hint">أداء إشارات الصعود فقط</div>
                </div>

                <div class="card">
                    <div class="card-title">🔴 نجاح الفرص الهابطة</div>
                    <div class="num put">{put_win_rate}%</div>
                    <div class="hint">أداء إشارات الهبوط فقط</div>
                </div>

                <div class="card">
                    <div class="card-title">📈 أفضل ظروف السوق</div>
                    <div class="big-text gold">{best_market_name}</div>
                    <div class="hint">نسبة النجاح: {group_rate(best_market_state)}% | عدد الإشارات: {group_total(best_market_state)}</div>
                </div>

                <div class="card">
                    <div class="card-title">⭐ أفضل درجة جودة</div>
                    <div class="big-text gold">{ar_score(best_score_name)}</div>
                    <div class="hint">نسبة النجاح: {group_rate(best_score)}% | عدد الإشارات: {group_total(best_score)}</div>
                </div>
            </div>

            <div class="cards2">
                <div class="card">
                    <div class="card-title">⏰ أفضل فريم أداءً</div>
                    <div class="big-text">{best_timeframe_name}</div>
                    <div class="hint">نسبة النجاح: {group_rate(best_timeframe)}% | عدد الإشارات: {group_total(best_timeframe)}</div>
                </div>

                <div class="card">
                    <div class="card-title">🏅 أفضل سهم / عملة أداءً</div>
                    <div class="big-text">{best_ticker_name}</div>
                    <div class="hint">نسبة النجاح: {group_rate(best_ticker)}% | عدد الإشارات: {group_total(best_ticker)}</div>
                </div>

                <div class="card">
                    <div class="card-title">ميزان النتائج</div>
                    <div class="big-text"><span class="win">{win_count} رابحة</span> / <span class="loss">{loss_count} خاسرة</span></div>
                    <div class="hint">يعكس أداء المؤشر بعد إغلاق الصفقات</div>
                </div>
            </div>

            <h2>📋 آخر الإشارات</h2>
            <table>
                <thead>
                    <tr>
                        <th>الرقم</th>
                        <th>وقت الإشارة</th>
                        <th>السهم / العملة</th>
                        <th>نوع الفرصة</th>
                        <th>الفريم</th>
                        <th>سعر الدخول</th>
                        <th>درجة الجودة</th>
                        <th>التذبذب %</th>
                        <th>هدف 1</th>
                        <th>هدف 2</th>
                        <th>هدف 3</th>
                        <th>حالة السوق</th>
                        <th>حالة الصفقة</th>
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


@app.get("/api/learning/run")
def run_learning():

    score_result = learn_best_score()
    market_result = learn_best_market_state()
    timeframe_result = learn_best_timeframe()
    ticker_result = learn_best_ticker()

    return {
        "score_learning": score_result,
        "market_learning": market_result,
        "timeframe_learning": timeframe_result,
        "ticker_learning": ticker_result
    }


@app.get("/api/learning")
def api_learning():
    return get_learning_insights()


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
