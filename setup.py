#!/usr/bin/env python3
"""سكريبت إعداد البوت"""
import os
import sys
import secrets


def generate_env():
    """توليد ملف .env"""
    print("🚀 إعداد بوت مكتبة الكتب الذكية")
    print("=" * 50)

    # جمع المعلومات
    bot_token = input("🔑 أدخل توكن البوت (من @BotFather): ").strip()
    owner_id = input("👤 أدخل معرف تليجرام الخاص بك: ").strip()

    openrouter_key = input("🤖 أدخل مفتاح OpenRouter (اختياري): ").strip()

    # توليد ملف .env
    env_content = f"""# Telegram Bot
BOT_TOKEN={bot_token}
OWNER_ID={owner_id}

# Database
DATABASE_URL=sqlite:///library.db

# AI Services
OPENROUTER_API_KEY={openrouter_key or ''}
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=google/gemini-2.5-flash-preview

# Application
DEBUG=True
PORT=8080

# Features
ENABLE_AI_SUMMARY=True
ENABLE_SEMANTIC_SEARCH=True
ENABLE_REFERRAL_SYSTEM=True
ENABLE_LEADERBOARD=True
ENABLE_COMMENTS=True
ENABLE_BATCH_UPLOAD=True
ENABLE_AI_INSIGHTS=True
ENABLE_NOTIFICATIONS=True
ENABLE_PACKS=True
"""

    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)

    print("
✅ تم إنشاء ملف .env")
    print("📁 يمكنك تعديل الإعدادات لاحقاً في ملف .env")

    # إنشاء قاعدة البيانات
    print("
🗄️ جاري إنشاء قاعدة البيانات...")
    try:
        from bot.database.models import Database
        db = Database("sqlite:///library.db")
        db.create_tables()
        print("✅ تم إنشاء قاعدة البيانات")
    except Exception as e:
        print(f"⚠️ خطأ في إنشاء قاعدة البيانات: {e}")

    print("
🎉 تم الإعداد بنجاح!")
    print("
لتشغيل البوت:")
    print("  python -m bot.main")


def create_admin():
    """إنشاء مستخدم أولي"""
    print("👑 إنشاء حساب المالك")
    # يمكن إضافة منطق هنا


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--generate-env":
        generate_env()
    else:
        print("الاستخدام: python scripts/setup.py --generate-env")
