"""لوحات المفاتيح المضمنة (Inline Keyboards)"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional


class InlineKeyboards:
    """مصنع لوحات المفاتيح المضمنة"""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """القائمة الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("📚 تصفح المكتبة", callback_data="browse_categories")],
            [InlineKeyboardButton("🔍 البحث الذكي", callback_data="smart_search")],
            [InlineKeyboardButton("❤️ مفضلتي", callback_data="my_favorites"),
             InlineKeyboardButton("📜 سجل التحميلات", callback_data="my_downloads")],
            [InlineKeyboardButton("👤 ملفي الشخصي", callback_data="my_profile"),
             InlineKeyboardButton("🏆 لوحة الشرف", callback_data="leaderboard")],
            [InlineKeyboardButton("🔗 رابط الإحالة", callback_data="my_referral")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def book_details(book_id: int, is_favorite: bool = False, is_owner: bool = False) -> InlineKeyboardMarkup:
        """لوحة تفاصيل الكتاب"""
        keyboard = [
            [InlineKeyboardButton("⬇️ تحميل الكتاب", callback_data=f"download_{book_id}")],
            [InlineKeyboardButton("📝 تلخيص AI", callback_data=f"ai_summary_{book_id}"),
             InlineKeyboardButton("💬 التعليقات", callback_data=f"comments_{book_id}")],
            [InlineKeyboardButton("⭐ تقييم", callback_data=f"rate_{book_id}"),
             InlineKeyboardButton("❤️ إزالة من المفضلة" if is_favorite else "❤️ إضافة للمفضلة", 
                                 callback_data=f"unfav_{book_id}" if is_favorite else f"fav_{book_id}")],
            [InlineKeyboardButton("🔗 مشاركة", callback_data=f"share_{book_id}"),
             InlineKeyboardButton("📚 كتب مشابهة", callback_data=f"similar_{book_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_books")],
        ]

        if is_owner:
            keyboard.insert(1, [
                InlineKeyboardButton("✏️ تعديل", callback_data=f"edit_book_{book_id}"),
                InlineKeyboardButton("❌ حذف", callback_data=f"delete_book_{book_id}")
            ])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def categories_list(categories: List, page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
        """قائمة الأقسام"""
        keyboard = []
        start = page * per_page
        end = start + per_page

        for cat in categories[start:end]:
            keyboard.append([InlineKeyboardButton(f"📁 {cat.name}", callback_data=f"cat_{cat.id}")])

        # أزرار التنقل
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ السابق", callback_data=f"cats_page_{page-1}"))
        if end < len(categories):
            nav_buttons.append(InlineKeyboardButton("التالي ▶️", callback_data=f"cats_page_{page+1}"))

        if nav_buttons:
            keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def books_list(books: List, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
        """قائمة الكتب"""
        keyboard = []
        start = page * per_page
        end = start + per_page

        for book in books[start:end]:
            author_name = book.author.name if book.author else "غير معروف"
            keyboard.append([InlineKeyboardButton(
                f"📖 {book.title} - {author_name}", 
                callback_data=f"book_{book.id}"
            )])

        # أزرار التنقل
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ السابق", callback_data=f"books_page_{page-1}"))
        if end < len(books):
            nav_buttons.append(InlineKeyboardButton("التالي ▶️", callback_data=f"books_page_{page+1}"))

        if nav_buttons:
            keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_categories")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def rating_stars(book_id: int) -> InlineKeyboardMarkup:
        """أزرار التقييم"""
        keyboard = [
            [InlineKeyboardButton("⭐", callback_data=f"rate_{book_id}_1"),
             InlineKeyboardButton("⭐⭐", callback_data=f"rate_{book_id}_2"),
             InlineKeyboardButton("⭐⭐⭐", callback_data=f"rate_{book_id}_3"),
             InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rate_{book_id}_4"),
             InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rate_{book_id}_5")],
            [InlineKeyboardButton("🔙 إلغاء", callback_data=f"book_{book_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def comments_list(comments: List, book_id: int, page: int = 0) -> InlineKeyboardMarkup:
        """قائمة التعليقات"""
        keyboard = []
        start = page * 5
        end = start + 5

        for comment in comments[start:end]:
            likes = comment.likes_count
            keyboard.append([InlineKeyboardButton(
                f"👤 {comment.user.first_name or 'مستخدم'}: {comment.content[:30]}... | ❤️ {likes}",
                callback_data=f"comment_{comment.id}"
            )])

        keyboard.append([InlineKeyboardButton("➕ إضافة تعليق", callback_data=f"add_comment_{book_id}")])

        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"comments_page_{book_id}_{page-1}"))
        if end < len(comments):
            nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"comments_page_{book_id}_{page+1}"))

        if nav_buttons:
            keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"book_{book_id}")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def comment_actions(comment_id: int, book_id: int, user_liked: bool = False) -> InlineKeyboardMarkup:
        """إجراءات التعليق"""
        keyboard = [
            [InlineKeyboardButton("❤️ إلغاء الإعجاب" if user_liked else "❤️ إعجاب", 
                                 callback_data=f"like_comment_{comment_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"comments_{book_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """قائمة المشرف"""
        keyboard = [
            [InlineKeyboardButton("📁 إدارة الأقسام", callback_data="admin_categories"),
             InlineKeyboardButton("📚 إدارة الكتب", callback_data="admin_books")],
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users"),
             InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 الإذاعة", callback_data="admin_broadcast"),
             InlineKeyboardButton("🤖 أدوات AI", callback_data="admin_ai_tools")],
            [InlineKeyboardButton("📋 القنوات الإجبارية", callback_data="admin_channels")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_delete(book_id: int) -> InlineKeyboardMarkup:
        """تأكيد الحذف"""
        keyboard = [
            [InlineKeyboardButton("✅ نعم، احذف", callback_data=f"confirm_delete_{book_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data=f"book_{book_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def packs_list(packs: List) -> InlineKeyboardMarkup:
        """قائمة الباقات"""
        keyboard = []
        for pack in packs:
            keyboard.append([InlineKeyboardButton(f"📦 {pack.name}", callback_data=f"pack_{pack.id}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def pack_items(items: List, pack_id: int) -> InlineKeyboardMarkup:
        """عناصر الباقة"""
        keyboard = []
        for item in items:
            status = "✅" if item.book.download_count > 0 else "⬜"
            keyboard.append([InlineKeyboardButton(
                f"{status} {item.order}. {item.book.title}",
                callback_data=f"book_{item.book_id}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="browse_packs")])
        return InlineKeyboardMarkup(keyboard)
