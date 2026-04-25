"""وسيط Rate Limiting"""
import logging
import time
from typing import Dict, Optional
from telegram import Update
from telegram.ext import ContextTypes
from bot.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimiter:
    """محدد معدل الرسائل"""

    def __init__(self):
        self.user_messages: Dict[int, list] = {}
        self.max_messages = settings.RATE_LIMIT_MESSAGES
        self.window = settings.RATE_LIMIT_WINDOW

    def is_allowed(self, user_id: int) -> bool:
        """التحقق مما إذا كان المستخدم مسموحاً له"""
        now = time.time()

        if user_id not in self.user_messages:
            self.user_messages[user_id] = []

        # إزالة الرسائل القديمة
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if now - msg_time < self.window
        ]

        if len(self.user_messages[user_id]) >= self.max_messages:
            return False

        self.user_messages[user_id].append(now)
        return True

    def get_wait_time(self, user_id: int) -> int:
        """الحصول على وقت الانتظار"""
        if user_id not in self.user_messages or not self.user_messages[user_id]:
            return 0

        now = time.time()
        oldest = min(self.user_messages[user_id])
        wait = int(self.window - (now - oldest))
        return max(0, wait)


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """الحصول على محدد المعدل"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def rate_limit_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """وسيط Rate Limiting"""
    if not update.effective_user:
        return True

    user_id = update.effective_user.id
    limiter = get_rate_limiter()

    if not limiter.is_allowed(user_id):
        wait_time = limiter.get_wait_time(user_id)
        if update.effective_message:
            await update.effective_message.reply_text(
                f"⏳ يرجى الانتظار {wait_time} ثانية قبل إرسال رسالة جديدة."
            )
        return False

    return True
