"""معالج أمر البدء"""
import logging
import secrets
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import User
from bot.config import get_settings
from bot.keyboards import InlineKeyboards
from bot.utils import generate_referral_code, parse_deep_link

logger = logging.getLogger(__name__)
settings = get_settings()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    user = update.effective_user
    db: Session = context.bot_data.get("db_session")

    if not db:
        await update.message.reply_text("❌ خطأ في الاتصال بقاعدة البيانات")
        return

    # التحقق من وجود المستخدم
    db_user = db.query(User).filter(User.telegram_id == user.id).first()

    if not db_user:
        # إنشاء مستخدم جديد
        referral_code = generate_referral_code(user.id)
        db_user = User(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code or "ar",
            referral_code=referral_code,
            total_points=0
        )

        # التحقق من الإحالة
        if context.args and len(context.args) > 0:
            start_param = context.args[0]
            ref_type, ref_value = parse_deep_link(start_param)

            if ref_type == "referral":
                # معالجة الإحالة
                referrer_id = ref_value.split("_")[1] if "_" in ref_value else None
                if referrer_id and int(referrer_id) != user.id:
                    referrer = db.query(User).filter(User.telegram_id == int(referrer_id)).first()
                    if referrer:
                        db_user.referred_by = referrer.telegram_id
                        referrer.total_points += 50
                        db_user.total_points += 10
                        db.add(db_user)
                        db.commit()

                        # إشعار المُحيل
                        try:
                            await context.bot.send_message(
                                referrer.telegram_id,
                                f"🎉 انضم مستخدم جديد عبر رابطك! حصلت على 50 نقطة."
                            )
                        except Exception:
                            pass

            elif ref_type == "book":
                # فتح كتاب محدد
                from bot.handlers.user.books import show_book_details
                await show_book_details(update, context, ref_value)
                return

        db.add(db_user)
        db.commit()

        welcome_text = f"""
🎉 أهلاً بك {user.first_name or 'صديقي'} في بوت مكتبة الكتب الذكية!

📚 مكتبة ضخمة من الكتب الإلكترونية
🤖 ذكاء اصطناعي للتلخيص والبحث
🏆 نظام نقاط ولوحة شرف
💬 تعليقات وتقييمات

اختر من القائمة أدناه:
"""
    else:
        welcome_text = f"""
👋 أهلاً بعودتك {user.first_name or 'صديقي'}!

📚 نقاطك: {db_user.total_points}
📖 تحميلاتك: {db_user.total_downloads}

اختر من القائمة:
"""

    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboards.main_menu()
    )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /profile"""
    user = update.effective_user
    db: Session = context.bot_data.get("db_session")

    if not db:
        return

    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    if not db_user:
        await update.message.reply_text("❌ لم يتم العثور على ملفك. اضغط /start")
        return

    from bot.utils import get_badge

    badge = get_badge(db_user.total_points)

    profile_text = f"""
👤 <b>ملفك الشخصي</b>

🆔 المعرف: <code>{user.id}</code>
👤 الاسم: {user.first_name or 'غير معروف'}
📛 اليوزر: @{user.username or 'لا يوجد'}

📊 <b>الإحصائيات:</b>
• 📖 عدد التحميلات: {db_user.total_downloads}
• ⭐ النقاط: {db_user.total_points}
• 🏅 الشارة: {badge}
• 📅 تاريخ الانضمام: {db_user.created_at.strftime('%Y-%m-%d') if db_user.created_at else 'غير معروف'}
"""

    await update.message.reply_text(profile_text, parse_mode="HTML")


async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /referral"""
    user = update.effective_user
    db: Session = context.bot_data.get("db_session")

    if not db:
        return

    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    if not db_user:
        await update.message.reply_text("❌ اضغط /start أولاً")
        return

    bot_info = await context.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={db_user.referral_code}"

    referral_text = f"""
🔗 <b>رابط الإحالة الخاص بك</b>

{referral_link}

🎁 <b>المكافآت:</b>
• أنت تحصل على 50 نقطة لكل صديق
• صديقك يحصل على 10 نقاط

📊 رصيدك الحالي: {db_user.total_points} نقطة
"""

    await update.message.reply_text(referral_text, parse_mode="HTML")
