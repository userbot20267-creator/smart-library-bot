"""وسيط المصادقة"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import User, RequiredChannel
from bot.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthMiddleware:
    """وسيط المصادقة والتصاريح"""

    @staticmethod
    async def check_banned(update: Update, db: Session) -> bool:
        """التحقق مما إذا كان المستخدم محظوراً"""
        if not update.effective_user:
            return False

        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if user and user.is_banned:
            await update.effective_message.reply_text(
                "🚷 تم حظرك من استخدام البوت."
            )
            return True
        return False

    @staticmethod
    async def check_required_channels(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session) -> bool:
        """التحقق من الاشتراك في القنوات الإجبارية"""
        channels = db.query(RequiredChannel).filter(RequiredChannel.is_active == True).all()

        if not channels:
            return True

        not_joined = []
        for channel in channels:
            try:
                member = await context.bot.get_chat_member(channel.channel_id, update.effective_user.id)
                if member.status in ['left', 'kicked']:
                    not_joined.append(channel)
            except Exception:
                pass

        if not_joined:
            text = "📢 يجب الاشتراك في القنوات التالية:\n\n"
            for ch in not_joined:
                link = f"https://t.me/{ch.channel_username}" if ch.channel_username else ch.channel_id
                text += f"• [{ch.channel_name or ch.channel_username}]({link})\n"

            text += "\n✅ بعد الاشتراك، اضغط /start"
            await update.effective_message.reply_text(text, parse_mode="Markdown")
            return False

        return True

    @staticmethod
    def is_owner(user_id: int) -> bool:
        """التحقق مما إذا كان المستخدم هو المالك"""
        return user_id == settings.OWNER_ID

    @staticmethod
    def is_admin(user: User) -> bool:
        """التحقق مما إذا كان المستخدم مشرفاً أو المالك (بما في ذلك عبر OWNER_ID)"""
        # إذا كان مسجلاً كمالك أو مشرف في قاعدة البيانات
        if user.is_admin or user.is_owner:
            return True
        # أو إذا كان رقمه مطابقاً لـ OWNER_ID في الإعدادات (يُعتبر مالكاً تلقائياً)
        if user.telegram_id == settings.OWNER_ID:
            return True
        return False
