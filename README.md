# 📚 بوت مكتبة الكتب الذكية

بوت تيليجرام متكامل لإدارة مكتبة كتب رقمية ضخمة مع دعم الذكاء الاصطناعي وميزات تفاعلية متقدمة.

## 🌟 المميزات

### للمستخدمين
- 📚 تصفح المكتبة حسب الأقسام
- 🔍 بحث ذكي دلالي (Semantic Search)
- 🤖 تلخيص الكتب بالذكاء الاصطناعي
- 💬 نظام تعليقات وإعجابات
- ❤️ قائمة مفضلة وسجل تحميلات
- ⭐ نظام تقييمات
- 🏆 نظام نقاط ولوحة شرف
- 🔗 نظام إحالة
- 📦 باقات تعليمية منظمة
- 🔔 إشعارات مخصصة

### للمالك
- 👑 لوحة تحكم كاملة
- 📚 إدارة الكتب والأقسام
- 🤖 أدوات ذكاء اصطناعي
- 🔍 بحث ذكي وإضافة تلقائية
- 📦 رفع دفعي لعدة كتب
- 📊 إحصائيات وتحليلات
- 📢 نظام إذاعة
- 👥 إدارة المستخدمين
- 📋 قنوات إجبارية

## 🏗️ البنية المعمارية

```
smart-library-bot/
├── bot/
│   ├── config/           # الإعدادات
│   ├── database/         # قاعدة البيانات والنماذج
│   ├── handlers/         # معالجات التليجرام
│   │   ├── user/         # معالجات المستخدم
│   │   └── admin/        # معالجات المشرف
│   ├── services/         # الخدمات
│   │   ├── ai/           # خدمة الذكاء الاصطناعي
│   │   ├── search/       # البحث الدلالي
│   │   └── embeddings/   # التمثيل الدلالي
│   ├── keyboards/        # لوحات المفاتيح
│   ├── middlewares/      # الوسطاء
│   ├── features/         # الميزات
│   │   ├── packs/        # نظام الباقات
│   │   ├── notifications/# الإشعارات
│   │   └── ...
│   ├── scheduler/        # الجدولة
│   └── main.py           # نقطة الدخول
├── docs/                 # التوثيق
├── tests/                # الاختبارات
├── requirements.txt      # المتطلبات
├── Procfile             # Railway
└── .env.example         # مثال للمتغيرات
```

## 🚀 التشغيل على Railway

### 1. إنشاء مشروع على Railway
```bash
# تثبيت Railway CLI
npm install -g @railway/cli

# تسجيل الدخول
railway login

# إنشاء مشروع
railway init
```

### 2. إعداد المتغيرات البيئية
```bash
railway variables set BOT_TOKEN="your_token"
railway variables set OWNER_ID="your_telegram_id"
railway variables set OPENROUTER_API_KEY="your_key"
railway variables set DATABASE_URL="${{Postgres.DATABASE_URL}}"
```

### 3. النشر
```bash
git add .
git commit -m "Initial commit"
git push

# أو عبر Railway CLI
railway up
```

### 4. إضافة PostgreSQL
- اذهب إلى Railway Dashboard
- أضف Plugin: PostgreSQL
- سيتم إنشاء متغير `DATABASE_URL` تلقائياً

## 🛠️ التشغيل محلياً

### المتطلبات
- Python 3.11+
- PostgreSQL (اختياري - يمكن استخدام SQLite للتطوير)

### التثبيت
```bash
# استنساخ المستودع
git clone https://github.com/yourusername/smart-library-bot.git
cd smart-library-bot

# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو: venv\Scripts\activate  # Windows

# تثبيت المتطلبات
pip install -r requirements.txt

# إعداد المتغيرات البيئية
cp .env.example .env
# عدل ملف .env بمعلوماتك

# التشغيل
python -m bot.main
```

## ⚙️ المتغيرات البيئية

| المتغير | الوصف | مطلوب |
|---------|-------|-------|
| `BOT_TOKEN` | توكن بوت تيليجرام | ✅ |
| `OWNER_ID` | معرف تليجرام للمالك | ✅ |
| `DATABASE_URL` | رابط قاعدة البيانات | ✅ |
| `OPENROUTER_API_KEY` | مفتاح OpenRouter | ❌ |
| `AI_MODEL` | نموذج AI | ❌ |
| `WEBHOOK_URL` | رابط Webhook | ❌ |
| `PORT` | المنفذ | ❌ |

## 📋 الأوامر

| الأمر | الوصف | للمالك |
|-------|-------|--------|
| `/start` | بدء البوت | ❌ |
| `/profile` | الملف الشخصي | ❌ |
| `/referral` | رابط الإحالة | ❌ |
| `/search` | البحث | ❌ |
| `/admin` | لوحة التحكم | ✅ |
| `/ai_search` | بحث ذكي | ✅ |
| `/ai_insights` | تحليل AI | ✅ |
| `/batch` | رفع دفعي | ✅ |

## 🧠 خدمة الذكاء الاصطناعي

يستخدم البوت:
- **OpenRouter** للوصول إلى نماذج Google Gemini
- **Sentence Transformers** للـ Embeddings
- **PyPDF2/pdfplumber** لاستخراج النص من PDF

## 📄 الترخيص

MIT License

## 🤝 المساهمة

نرحب بمساهماتكم! يمكنك:
- فتح Issue للإبلاغ عن مشكلة
- إرسال Pull Request
- اقتراح ميزات جديدة

## 📞 التواصل

للدعم والاستفسارات، تواصل معنا عبر تيليجرام.

---

<div align="center">
  <b>صنع بحب ❤️ للقراء والمكتبات الرقمية</b>
</div>
