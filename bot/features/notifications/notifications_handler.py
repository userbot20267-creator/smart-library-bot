"""نظام الإشعارات المخصصة"""
import logging
import json
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import User, Book, Author, Category, Notification

logger = logging.getLogger(__name__)


async def notification_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعدادات الإشعارات"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    if not db_user:
        return

    keyboard = [
        [InlineKeyboardButton(
            f"📚 كتب جديدة: {'✅' if db_user.notify_new_books else '❌'}", 
            callback_data="toggle_notify_books"
        )],
        [InlineKeyboardButton(
            f"✍️ مؤلفين جدد: {'✅' if db_user.notify_new_authors else '❌'}",
            callback_data="toggle_notify_authors"
        )],
        [InlineKeyboardButton("📁 إدارة الأقسام المفضلة", callback_data="manage_pref_cats")],
        [InlineKeyboardButton("✍️ إدارة المؤلفين المفضلين", callback_data="manage_pref_authors")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ]

    await query.edit_message_text(
        "🔔 <b>إعدادات الإشعارات</b>

"
        "اختر ما تريد:
"
        "• استلام إشعارات عند إضافة كتب جديدة
"
        "• متابعة مؤلفين محددين
"
        "• متابعة أقسام محددة",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def toggle_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تبديل إعداد الإشعارات"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    db_user = db.query(User).filter(User.telegram_id == user.id).first()

    if query.data == "toggle_notify_books":
        db_user.notify_new_books = not db_user.notify_new_books
        status = "مفعل" if db_user.notify_new_books else "معطل"
        await query.answer(f"🔔 إشعارات الكتب: {status}")
    elif query.data == "toggle_notify_authors":
        db_user.notify_new_authors = not db_user.notify_new_authors
        status = "مفعل" if db_user.notify_new_authors else "معطل"
        await query.answer(f"🔔 إشعارات المؤلفين: {status}")

    db.commit()
    await notification_settings(update, context)


async def manage_preferred_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة الأقسام المفضلة"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    preferred = json.loads(db_user.preferred_categories) if db_user.preferred_categories else []

    categories = db.query(Category).all()
    keyboard = []

    for cat in categories:
        is_selected = cat.id in preferred
        icon = "✅" if is_selected else "⬜"
        keyboard.append([InlineKeyboardButton(
            f"{icon} {cat.name}",
            callback_data=f"prefcat_{cat.id}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="notification_settings")])

    await query.edit_message_text(
        "📁 <b>الأقسام المفضلة</b>

"
        "اختر الأقسام التي تريد متابعتها:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def toggle_preferred_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تبديل قسم مفضل"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    category_id = int(query.data.split("_")[1])
    db_user = db.query(User).filter(User.telegram_id == user.id).first()

    preferred = json.loads(db_user.preferred_categories) if db_user.preferred_categories else []

    if category_id in preferred:
        preferred.remove(category_id)
        await query.answer("❌ تمت الإزالة")
    else:
        preferred.append(category_id)
        await query.answer("✅ تمت الإضافة")

    db_user.preferred_categories = json.dumps(preferred)
    db.commit()

    await manage_preferred_categories(update, context)


async def notify_users_new_book(context: ContextTypes.DEFAULT_TYPE, book: Book):
    """إشعار المستخدمين بكتاب جديد"""
    db: Session = context.bot_data.get("db_session")
    if not db:
        return

    # المستخدمين الذين يريدون إشعارات الكتب
    users = db.query(User).filter(
        User.notify_new_books == True,
        User.is_banned == False
    ).all()

    # تصفية حسب الأقسام المفضلة
    notified = 0
    for user in users:
        preferred = json.loads(user.preferred_categories) if user.preferred_categories else []

        # إذا لم يحدد أقسام مفضلة أو القسم في القائمة
        if not preferred or (book.category_id and book.category_id in preferred):
            try:
                text = f"""
📚 <b>كتاب جديد!</b>

📖 {book.title}
✍️ {book.author.name if book.author else 'غير معروف'}
📁 {book.category.name if book.category else 'غير مصنف'}

اضغط لتحميله!
"""
                await context.bot.send_message(
                    user.telegram_id,
                    text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📖 عرض الكتاب", callback_data=f"book_{book.id}")]
                    ])
                )
                notified += 1
            except Exception as e:
                logger.error(f"Notification error: {e}")

    logger.info(f"Notified {notified} users about new book: {book.title}")


async def manage_preferred_authors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة المؤلفين المفضلين"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    preferred = json.loads(db_user.preferred_authors) if db_user.preferred_authors else []

    authors = db.query(Author).limit(30).all()
    keyboard = []

    for author in authors:
        is_selected = author.id in preferred
        icon = "✅" if is_selected else "⬜"
        keyboard.append([InlineKeyboardButton(
            f"{icon} {author.name}",
            callback_data=f"prefauth_{author.id}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="notification_settings")])

    await query.edit_message_text(
        "✍️ <b>المؤلفين المفضلين</b>

"
        "اختر المؤلفين الذين تريد متابعتهم:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def toggle_preferred_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تبديل مؤلف مفضل"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    author_id = int(query.data.split("_")[1])
    db_user = db.query(User).filter(User.telegram_id == user.id).first()

    preferred = json.loads(db_user.preferred_authors) if db_user.preferred_authors else []

    if author_id in preferred:
        preferred.remove(author_id)
        await query.answer("❌ تمت الإزالة")
    else:
        preferred.append(author_id)
        await query.answer("✅ تمت الإضافة")

    db_user.preferred_authors = json.dumps(preferred)
    db.commit()

    await manage_preferred_authors(update, context)
