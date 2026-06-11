# Smart Learning Engine V1

موقع بسيط يستقبل إشارات TradingView Webhook، يحفظها في SQLite، ويعرض Dashboard.

## التشغيل على جهازك

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

ثم افتح:

```text
http://127.0.0.1:8000
```

## رابط Webhook

ضع هذا الرابط في TradingView بعد رفع الموقع:

```text
https://YOUR-DOMAIN.com/webhook/tradingview
```

## تجربة سريعة

```bash
curl -X POST http://127.0.0.1:8000/webhook/tradingview \
-H "Content-Type: application/json" \
-d '{"ticker":"AAPL","signal":"CALL","timeframe":"30","price":"195.20","score":"5","atr":"3.10","atr_pct":"1.8","target1":"198.30","target2":"199.85","target3":"201.40","rf_state":"CALL","rqk_state":"CALL","rp_state":"CALL_BREAK","market_state":"BULL_TREND","status":"OPEN"}'
```
