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
    learn_all_settings,
    generate_ai_recommendation
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
            body{{
                background:#020617;
                color:white;
                font-family:Arial;
                padding:40px;
            }}

            .card{{
                background:#111827;
                border:1px solid #374151;
                border-radius:16px;
                padding:20px;
                margin-bottom:20px;
            }}

            h1{{
                color:#f97316;
            }}

            h2{{
                color:#38bdf8;
            }}

            ul{{
                line-height:2;
            }}
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
       <title>🧭 بوصلة الفرص | Smart Learning Engine</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background:
                    radial-gradient(circle at top right, rgba(250,204,21,0.22), transparent 24%),
                    radial-gradient(circle at top left, rgba(56,189,248,0.16), transparent 26%),
                    radial-gradient(circle at bottom left, rgba(34,197,94,0.12), transparent 28%),
                    #020617;
                color:#e5e7eb;
                margin:0;
                padding:24px;
            }}
            .container {{
                max-width:1800px;
                margin:auto;
            }}
            .hero {{
                background:linear-gradient(135deg, rgba(15,23,42,0.92), rgba(2,6,23,0.98));
                border:1px solid rgba(250,204,21,0.30);
                border-radius:28px;
                padding:28px;
                margin-bottom:24px;
                box-shadow:0 0 45px rgba(250,204,21,0.12);
            }}
            h1 {{
                color:#facc15;
                font-size:58px;
                margin:0 0 8px 0;
                text-shadow:0 0 18px rgba(250,204,21,0.45);
            }}
            .subtitle {{
                color:#cbd5e1;
                font-size:18px;
                margin-bottom:18px;
            }}
            .badge {{
                display:inline-block;
                background:linear-gradient(90deg,#065f46,#047857);
                color:white;
                padding:9px 16px;
                border-radius:999px;
                font-size:13px;
                box-shadow:0 0 20px rgba(16,185,129,0.30);
            }}
            .quote {{
                margin-top:18px;
                background:rgba(15,23,42,0.75);
                border:1px solid rgba(249,115,22,0.45);
                border-right:5px solid #f97316;
                border-radius:18px;
                padding:16px 20px;
                color:#fef3c7;
                line-height:1.9;
            }}
            .quote b {{
                color:#f97316;
            }}
            h2 {{
                color:#f9fafb;
                margin-top:28px;
                margin-bottom:16px;
                font-size:26px;
            }}
            .cards {{
                display:grid;
                grid-template-columns:repeat(5,1fr);
                gap:14px;
                margin-bottom:18px;
            }}
            .cards3 {{
                display:grid;
                grid-template-columns:repeat(3,1fr);
                gap:14px;
                margin-bottom:20px;
            }}
            .card {{
                background:linear-gradient(145deg, rgba(15,23,42,0.96), rgba(2,6,23,0.98));
                border:1px solid rgba(56,189,248,0.28);
                border-radius:22px;
                padding:20px;
                box-shadow:0 0 28px rgba(56,189,248,0.12), inset 0 0 20px rgba(255,255,255,0.025);
                position:relative;
                overflow:hidden;
            }}
            .card::after {{
                content:"";
                position:absolute;
                width:95px;
                height:95px;
                border-radius:50%;
                background:rgba(250,204,21,0.07);
                left:-28px;
                bottom:-28px;
            }}
            .card-title {{
                color:#94a3b8;
                font-size:13px;
            }}
            .num {{
                font-size:36px;
                font-weight:bold;
                margin-top:10px;
            }}
            .win {{ color:#22c55e; font-weight:bold; }}
            .loss {{ color:#ef4444; font-weight:bold; }}
            .open {{ color:#facc15; font-weight:bold; }}
            .target {{ color:#38bdf8; font-weight:bold; }}
            .hint {{
                color:#94a3b8;
                font-size:12px;
                margin-top:6px;
            }}
            .bar {{
                height:9px;
                background:#1f2937;
                border-radius:999px;
                margin-top:12px;
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
                background:rgba(15,23,42,0.92);
                border-radius:18px;
                overflow:hidden;
                box-shadow:0 0 30px rgba(0,0,0,0.35);
                border:1px solid rgba(56,189,248,0.18);
            }}
            th, td {{
                border-bottom:1px solid rgba(55,65,81,0.8);
                padding:12px;
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
            .footer-note {{
                margin-top:16px;
                color:#94a3b8;
                font-size:13px;
                text-align:center;
            }}
            @media (max-width: 1100px) {{
                .cards, .cards3 {{
                    grid-template-columns:repeat(2,1fr);
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">

            <div class="hero">
                <h1>🧭 بوصلة الفرص</h1>
                <div class="badge">النظام نشط ✅ | استقبال الإشارات فعال ✅ | تتبع WIN / LOSS يعمل 🎯</div>
                <p class="subtitle">لوحة احترافية لمتابعة أداء إشارات بوصلة الفرص القادمة من TradingView.</p>

                <div class="quote">
                    <b>قاعدة التداول:</b>
                    لا تطارد السوق، ولا تدخل بلا خطة. الصبر على الفرصة أقوى من كثرة الدخول.
                    الربح لا يأتي من كل إشارة، بل من الالتزام بالاستراتيجية وإدارة الصفقة حتى نهايتها.
                </div>
            </div>

            <h2>📊 أداء بوصلة الفرص</h2>
            <div class="cards">
                <div class="card">
                    <div class="card-title">إجمالي الإشارات</div>
                    <div class="num">{total}</div>
                    <div class="hint">كل الفرص المسجلة</div>
                </div>

                <div class="card">
                    <div class="card-title">نسبة النجاح</div>
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

            <div class="cards3">
                <div class="card">
                    <div class="card-title">🎯 تحقق الهدف الأول</div>
                    <div class="num target">{target1_hit}</div>
                    <div class="hint">{target1_rate}% من إجمالي الإشارات</div>
                    <div class="bar"><div class="bar-fill" style="width:{target1_rate}%"></div></div>
                </div>

                <div class="card">
                    <div class="card-title">🟢 نجاح الفرص الصاعدة</div>
                    <div class="num win">{call_win_rate}%</div>
                    <div class="hint">أداء إشارات CALL فقط</div>
                </div>

                <div class="card">
                    <div class="card-title">🔴 نجاح الفرص الهابطة</div>
                    <div class="num loss">{put_win_rate}%</div>
                    <div class="hint">أداء إشارات PUT فقط</div>
                </div>
            </div>

            <div class="cards3">
                <div class="card">
                    <div class="card-title">ميزان النتائج</div>
                    <div class="num"><span class="win">{win_count}</span> / <span class="loss">{loss_count}</span></div>
                    <div class="hint">رابحة / خاسرة</div>
                </div>

                <div class="card">
                    <div class="card-title">حالة النظام</div>
                    <div class="num win">نشط</div>
                    <div class="hint">جاهز لاستقبال إشارات الأسهم</div>
                </div>

                <div class="card">
                    <div class="card-title">مرحلة البيانات</div>
                    <div class="num target">حقيقية</div>
                    <div class="hint">بعد تنظيف بيانات الاختبار</div>
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
                هذه اللوحة للتعلّم والتحليل وليست توصية شراء أو بيع. .
            </div>
        </div>
    </body>
    </html>
"""


@app.get("/api/learning/run")
def run_learning():
    return learn_all_settings()


@app.get("/api/learning/recommendation")
def ai_recommendation():
    return generate_ai_recommendation()


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
