"""دوال مساعدة"""
import random
import string
import hashlib
from datetime import datetime, timedelta
from typing import Optional


def generate_referral_code(telegram_id: int) -> str:
    """توليد كود إحالة فريد"""
    base = f"{telegram_id}{datetime.now().timestamp()}"
    hash_obj = hashlib.md5(base.encode()).hexdigest()[:6]
    return f"ref_{telegram_id}_{hash_obj}"


def generate_id() -> str:
    """توليد ID عشوائي"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


def format_file_size(size_bytes: int) -> str:
    """تنسيق حجم الملف"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def escape_markdown(text: str) -> str:
    """تخطي أحرف Markdown"""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, f'\\{char}')
    return text


def truncate_text(text: str, max_length: int = 4000) -> str:
    """اقتصاص النص"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def get_badge(points: int) -> str:
    """الحصول على الشارة بناءً على النقاط"""
    if points >= 1000:
        return "👑 قارئ أسطوري"
    elif points >= 500:
        return "🥇 قارئ محترف"
    elif points >= 200:
        return "🥈 قارئ نهم"
    elif points >= 50:
        return "📚 قارئ نشط"
    else:
        return "📖 قارئ مبتدئ"


def parse_deep_link(start_param: str) -> tuple:
    """تحليل الرابط العميق"""
    if start_param.startswith("book_"):
        return ("book", int(start_param.replace("book_", "")))
    elif start_param.startswith("ref_"):
        return ("referral", start_param)
    return ("unknown", start_param)


def format_datetime(dt: Optional[datetime]) -> str:
    """تنسيق التاريخ"""
    if not dt:
        return "غير معروف"
    return dt.strftime("%Y-%m-%d %H:%M")
