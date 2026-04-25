# 🚀 دليل النشر على Railway

## الخطوة 1: إعداد المشروع

### إنشاء مستودع GitHub
1. أنشئ مستودعاً جديداً على GitHub
2. ارفع الملفات:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/smart-library-bot.git
git push -u origin main
```

## الخطوة 2: إعداد Railway

### الطريقة 1: عبر GitHub
1. سجل دخولك إلى [Railway](https://railway.app)
2. اضغط "New Project"
3. اختر "Deploy from GitHub repo"
4. اختر مستودع `smart-library-bot`
5. اضغط "Add Variables"

### الطريقة 2: عبر CLI
```bash
# تثبيت Railway CLI
npm install -g @railway/cli

# تسجيل الدخول
railway login

# ربط المشروع
railway link

# إضافة المتغيرات
railway variables set BOT_TOKEN="your_bot_token"
railway variables set OWNER_ID="123456789"
railway variables set OPENROUTER_API_KEY="your_key"
```

## الخطوة 3: إضافة قاعدة البيانات

1. في Railway Dashboard، اضغط "New"
2. اختر "Database" → "Add PostgreSQL"
3. سيتم إنشاء `DATABASE_URL` تلقائياً

## الخطوة 4: إعداد Webhook

### الحصول على Domain
1. في Railway Dashboard، اذهب إلى Settings
2. اضغط "Generate Domain"
3. انسخ الرابط (مثال: `https://your-app.up.railway.app`)

### إضافة المتغيرات
```bash
railway variables set WEBHOOK_URL="https://your-app.up.railway.app"
railway variables set PORT="8080"
```

## الخطوة 5: إعداد BotFather

1. افتح [@BotFather](https://t.me/BotFather)
2. أرسل `/setwebhook`
3. اختر بوتك
4. أرسل: `https://your-app.up.railway.app/YOUR_BOT_TOKEN`

## الخطوة 6: التحقق من النشر

1. اضغط على رابط Domain
2. يجب أن ترى "Bot is running!"
3. اختبر البوت على تيليجرام

## 🔧 استكشاف الأخطاء

### مشكلة: البوت لا يستجيب
- تأكد من صحة `BOT_TOKEN`
- تحقق من سجلات Railway Logs
- تأكد من تعيين `WEBHOOK_URL` بشكل صحيح

### مشكلة: قاعدة البيانات
- تأكد من إضافة PostgreSQL
- تحقق من صحة `DATABASE_URL`
- Railway يحول `postgres://` إلى `postgresql://` تلقائياً

### مشكلة: الذكاء الاصطناعي
- تأكد من صحة `OPENROUTER_API_KEY`
- تحقق من الرصيد في OpenRouter
- جرب نموذجاً آخر إذا كان النموذج الحالي لا يعمل

## 📊 مراقبة الأداء

### Railway Dashboard
- CPU Usage
- Memory Usage
- Network
- Logs

### إضافة New Relic (اختياري)
```bash
railway variables set NEW_RELIC_LICENSE_KEY="your_key"
```
