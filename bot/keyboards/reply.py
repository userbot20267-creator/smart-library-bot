"""لوحات المفاتيح العادية (Reply Keyboards)"""
from telegram import ReplyKeyboardMarkup, KeyboardButton


class ReplyKeyboards:
    """مصنع لوحات المفاتيح العادية"""

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """القائمة الرئيسية"""
        keyboard = [
            ["📚 تصفح المكتبة", "🔍 بحث"],
            ["❤️ المفضلة", "📜 التحميلات"],
            ["👤 ملفي", "🏆 لوحة الشرف"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def cancel() -> ReplyKeyboardMarkup:
        """زر إلغاء"""
        keyboard = [["❌ إلغاء"]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def admin_menu() -> ReplyKeyboardMarkup:
        """قائمة المشرف"""
        keyboard = [
            ["📁 الأقسام", "📚 الكتب"],
            ["👥 المستخدمين", "📊 الإحصائيات"],
            ["📢 إذاعة", "🔙 رجوع"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
