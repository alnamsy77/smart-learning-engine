import math
import time
from datetime import datetime, timezone

import yfinance as yf

CACHE_SECONDS = 60 * 30
_CACHE = {"time": 0, "data": None}

SECTORS = {
    "XLK": "التقنية",
    "XLC": "الاتصالات",
    "XLI": "الصناعي",
    "XLV": "الصحي",
    "XLE": "الطاقة",
    "XLB": "المواد",
    "XLRE": "العقاري",
    "XLF": "المالي",
    "XLY": "الاستهلاكي الكمالي",
    "XLP": "الاستهلاكي الأساسي",
    "XLU": "المرافق",
}

# قائمة احتياطية واسعة من أسهم S&P500 في حال تعذر تحميل القائمة من الإنترنت.
# الهدف ألا تتعطل اللوحة أبداً.
BREADTH_FALLBACK = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","AVGO","TSLA","BRK-B",
    "JPM","LLY","V","XOM","UNH","MA","COST","WMT","HD","PG","NFLX","JNJ",
    "ABBV","BAC","KO","PM","CRM","ORCL","CVX","WFC","AMD","CSCO","ABT","MCD",
    "GE","IBM","LIN","MRK","TMO","ACN","ISRG","PEP","DIS","NOW","QCOM","CAT",
    "VZ","INTU","TXN","AMGN","UBER","BKNG","SPGI","PFE","RTX","LOW","HON",
    "NEE","GS","ETN","UNP","PGR","BLK","BA","TJX","SYK","C","DE","ADBE",
    "PANW","GILD","VRTX","LMT","ADI","MMC","MDT","ADP","CB","AMAT","PLD",
    "SBUX","COP","MO","SO","ELV","CI","KLAC","BSX","NKE","DUK","MDLZ","ICE",
]

def _clamp(value, low=0, high=100):
    try:
        return max(low, min(high, float(value)))
    except Exception:
        return 0

def _last(series):
    s = series.dropna()
    return float(s.iloc[-1]) if len(s) else None

def _decision(score):
    if score >= 85:
        return {"label": "شراء قوي", "color": "green", "tone": "إقبال قوي على المخاطرة"}
    if score >= 70:
        return {"label": "شراء انتقائي", "color": "yellow", "tone": "السوق جيد لكن يحتاج انتقاء"}
    if score >= 50:
        return {"label": "حذر", "color": "orange", "tone": "السوق غير واضح"}
    return {"label": "خارج السوق", "color": "red", "tone": "العزوف عن المخاطرة أعلى"}

def _macd(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    line = ema12 - ema26
    signal = line.ewm(span=9, adjust=False).mean()
    hist = line - signal
    return line, signal, hist

def _ticker_trend_score(symbol):
    data = yf.download(symbol, period="3y", interval="1d", progress=False, auto_adjust=True)
    if data is None or data.empty:
        return 50

    close = data["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    weekly = close.resample("W-FRI").last().dropna()
    if len(weekly) < 40:
        return 50

    sma20w = weekly.rolling(20).mean()
    macd_line, macd_signal, hist = _macd(weekly)

    price = _last(weekly)
    ma = _last(sma20w)
    m = _last(macd_line)
    sig = _last(macd_signal)
    h = _last(hist)

    score = 0
    if price and ma and price > ma:
        score += 45
    if m is not None and sig is not None and m > sig:
        score += 35
    if h is not None and h > 0:
        score += 20

    return _clamp(score)

def _trend_score():
    spy = _ticker_trend_score("SPY")
    qqq = _ticker_trend_score("QQQ")
    return round((spy + qqq) / 2, 1), {"SPY": spy, "QQQ": qqq}

def _sector_score(symbol):
    data = yf.download(symbol, period="1y", interval="1d", progress=False, auto_adjust=True)
    if data is None or data.empty:
        return 50

    close = data["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]
    close = close.dropna()

    if len(close) < 80:
        return 50

    last = close.iloc[-1]
    prev5 = close.iloc[-6] if len(close) >= 6 else close.iloc[0]
    prev20 = close.iloc[-21] if len(close) >= 21 else close.iloc[0]

    perf_5d = ((last / prev5) - 1) * 100
    perf_20d = ((last / prev20) - 1) * 100

    macd_line, macd_signal, hist = _macd(close)
    h = _last(hist)

    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]

    # الأداء 40%
    perf_score = _clamp(50 + (perf_5d * 6) + (perf_20d * 2))

    # الزخم 30%
    momentum_score = 50
    if _last(macd_line) is not None and _last(macd_signal) is not None and _last(macd_line) > _last(macd_signal):
        momentum_score += 25
    if h is not None and h > 0:
        momentum_score += 25
    momentum_score = _clamp(momentum_score)

    # المتوسطات 30%
    ma_score = 0
    if last > sma20:
        ma_score += 50
    if last > sma50:
        ma_score += 50

    final = (perf_score * 0.40) + (momentum_score * 0.30) + (ma_score * 0.30)

    money_flow = round((perf_5d * 0.60) + (perf_20d * 0.40), 2)

    return round(_clamp(final), 1), money_flow

def _liquidity_score():
    items = []
    for symbol, name in SECTORS.items():
        score, flow = _sector_score(symbol)
        items.append({
            "symbol": symbol,
            "name": name,
            "score": score,
            "flow": flow,
            "status": "دخول قوي" if score >= 80 else "دخول متوسط" if score >= 65 else "محايد" if score >= 50 else "خروج سيولة"
        })

    items = sorted(items, key=lambda x: x["score"], reverse=True)
    avg = round(sum(x["score"] for x in items) / len(items), 1) if items else 50
    return avg, items

def _vix_score():
    data = yf.download("^VIX", period="3mo", interval="1d", progress=False, auto_adjust=True)
    if data is None or data.empty:
        return 50, None, "غير متاح"

    close = data["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    vix = _last(close)
    if vix is None:
        return 50, None, "غير متاح"

    if vix <= 14:
        score, label = 95, "هادئ جداً"
    elif vix <= 18:
        score, label = 85, "هادئ"
    elif vix <= 22:
        score, label = 70, "طبيعي"
    elif vix <= 28:
        score, label = 45, "مرتفع"
    else:
        score, label = 20, "خوف مرتفع"

    return score, round(vix, 2), label

def _breadth_score():
    # V1: محاولة حساب اتساع السوق من عينة واسعة احتياطية.
    # لاحقاً يمكن ربط القائمة الكاملة لـ S&P500.
    symbols = BREADTH_FALLBACK
    try:
        data = yf.download(symbols, period="260d", interval="1d", progress=False, auto_adjust=True, threads=True)
        if data is None or data.empty:
            return 50, 0, 0

        close = data["Close"]
        above50 = 0
        valid = 0

        for sym in symbols:
            try:
                s = close[sym].dropna()
                if len(s) < 60:
                    continue
                valid += 1
                if s.iloc[-1] > s.rolling(50).mean().iloc[-1]:
                    above50 += 1
            except Exception:
                continue

        pct = round((above50 / valid) * 100, 1) if valid else 50
        return pct, above50, valid
    except Exception:
        return 50, 0, 0

def _momentum_score(trend_details):
    # متوسط زخم SPY و QQQ من نفس محرك الاتجاه.
    return round((trend_details.get("SPY", 50) + trend_details.get("QQQ", 50)) / 2, 1)

def _week_score():
    # V1 مؤقت: درجة ثابتة معتدلة إلى أن نربط التقويم الاقتصادي.
    return 80

def get_market_mood(force_refresh=False):
    now = time.time()
    if not force_refresh and _CACHE["data"] and now - _CACHE["time"] < CACHE_SECONDS:
        return _CACHE["data"]

    try:
        trend, trend_details = _trend_score()
        liquidity, sectors = _liquidity_score()
        breadth, breadth_count, breadth_total = _breadth_score()
        momentum = _momentum_score(trend_details)
        volatility, vix_value, vix_label = _vix_score()
        week = _week_score()

        final_score = round(
            (trend * 0.35) +
            (liquidity * 0.25) +
            (breadth * 0.20) +
            (momentum * 0.10) +
            (volatility * 0.05) +
            (week * 0.05),
            1
        )

        decision = _decision(final_score)

        data = {
            "ok": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "score": final_score,
            "decision": decision,
            "gauges": {
                "الاتجاه العام": trend,
                "السيولة": liquidity,
                "قوة السوق": breadth,
                "الزخم": momentum,
                "التقلب": volatility,
                "ظروف الأسبوع": week,
            },
            "vix": {
                "value": vix_value,
                "label": vix_label,
                "score": volatility
            },
            "breadth": {
                "score": breadth,
                "above_50": breadth_count,
                "total": breadth_total
            },
            "sectors": sectors,
            "weights": {
                "الاتجاه العام": 35,
                "السيولة": 25,
                "قوة السوق": 20,
                "الزخم": 10,
                "التقلب": 5,
                "ظروف الأسبوع": 5,
            }
        }

        _CACHE["time"] = now
        _CACHE["data"] = data
        return data

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "score": 0,
            "decision": {"label": "غير متاح", "color": "red", "tone": "تعذر جلب بيانات السوق"},
            "gauges": {},
            "sectors": []
        }

