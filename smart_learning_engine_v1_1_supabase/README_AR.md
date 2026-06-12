# Smart Learning Engine V1.1 - Supabase

هذه النسخة تحفظ إشارات TradingView في Supabase PostgreSQL بدل SQLite.

## المطلوب في Render

أضف Environment Variable باسم:

DATABASE_URL

وقيمته رابط PostgreSQL من Supabase.

## التشغيل

uvicorn app:app --reload

## Webhook

https://YOUR-RENDER-APP.onrender.com/webhook/tradingview
