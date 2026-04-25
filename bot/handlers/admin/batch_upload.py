"""الرفع الدفعي المباشر للكتب"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationTypes
from sqlalchemy.orm import Session
from bot.database.models import Book, Category, Author
from bot.services import get_ai_service
from bot.keyboards import InlineKeyboards

logger = logging.getLogger(__name__)

# حالات المحادثة
BATCH_SELECT_CATEGORY = 1
BATCH_SELECT_AUTHOR = 2
BATCH_CONFIRM = 3


async def batch_upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء الرفع الدفعي"""
    user = update.effective_user
    db: Session = context.bot_data.get("db_session")

    if not db:
        await update.message.reply_text("❌ خطأ")
        return

    from bot.middlewares import AuthMiddleware
    db_user = db.query(User).filter(User.telegram_id == user.id).first()

    if not db_user or not AuthMiddleware.is_admin(db_user):
        await update.message.reply_text("🚷 ليس لديك صلاحية.")
        return

    await update.message.reply_text(
        "📦 <b>الرفع الدفعي</b>

"
        "أرسل جميع ملفات PDF التي تريد رفعها في رسالة واحدة أو متعددة.
"
        "ثم اضغط /done عند الانتهاء.

"
        "أو اضغط /cancel للإلغاء.",
        parse_mode="HTML"
    )

    context.user_data["batch_files"] = []
    context.user_data["batch_mode"] = True
    return BATCH_SELECT_CATEGORY


async def collect_batch_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جمع ملفات الرفع الدفعي"""
    if not context.user_data.get("batch_mode"):
        return

    if update.message.document and update.message.document.mime_type == "application/pdf":
        file_info = {
            "file_id": update.message.document.file_id,
            "file_name": update.message.document.file_name,
            "file_size": update.message.document.file_size,
            "title": update.message.document.file_name.replace(".pdf", "").replace("_", " ")
        }
        context.user_data["batch_files"].append(file_info)

        count = len(context.user_data["batch_files"])
        await update.message.reply_text(f"📎 تم استلام الملف ({count} ملفات حالياً). أرسل المزيد أو اضغط /done")
    else:
        await update.message.reply_text("❌ يرجى إرسال ملفات PDF فقط.")


async def batch_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتهاء جمع الملفات"""
    files = context.user_data.get("batch_files", [])

    if not files:
        await update.message.reply_text("❌ لم يتم استلام أي ملفات.")
        return ConversationHandler.END

    db: Session = context.bot_data.get("db_session")
    categories = db.query(Category).all()

    keyboard = [[InlineKeyboardButton(cat.name, callback_data=f"batchcat_{cat.id}")] for cat in categories]
    keyboard.append([InlineKeyboardButton("🆕 قسم جديد", callback_data="batch_new_cat")])

    await update.message.reply_text(
        f"📦 تم استلام {len(files)} ملفات.

"
        f"اختر القسم لهذه الكتب:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return BATCH_SELECT_AUTHOR


async def batch_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار القسم للرفع الدفعي"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")

    if query.data.startswith("batchcat_"):
        category_id = int(query.data.split("_")[1])
        context.user_data["batch_category_id"] = category_id
    elif query.data == "batch_new_cat":
        await query.edit_message_text("أرسل اسم القسم الجديد:")
        # يمكن إضافة معالج هنا
        return

    # عرض المؤلفين
    authors = db.query(Author).limit(20).all()
    keyboard = [[InlineKeyboardButton(auth.name, callback_data=f"batchauth_{auth.id}")] for auth in authors]
    keyboard.append([InlineKeyboardButton("🆕 مؤلف جديد", callback_data="batch_new_auth")])
    keyboard.append([InlineKeyboardButton("⏭️ تخطي", callback_data="batch_skip_auth")])

    await query.edit_message_text(
        "✍️ اختر المؤلف (اختياري):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return BATCH_CONFIRM


async def batch_select_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار المؤلف للرفع الدفعي"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")

    if query.data.startswith("batchauth_"):
        author_id = int(query.data.split("_")[1])
        context.user_data["batch_author_id"] = author_id
    elif query.data == "batch_new_auth":
        await query.edit_message_text("أرسل اسم المؤلف الجديد:")
        return

    # تأكيد الرفع
    files = context.user_data.get("batch_files", [])
    category_id = context.user_data.get("batch_category_id")
    author_id = context.user_data.get("batch_author_id")

    category = db.query(Category).filter(Category.id == category_id).first() if category_id else None
    author = db.query(Author).filter(Author.id == author_id).first() if author_id else None

    text = f"""
📦 <b>تأكيد الرفع الدفعي</b>

📁 القسم: {category.name if category else 'غير محدد'}
✍️ المؤلف: {author.name if author else 'غير محدد'}
📚 عدد الكتب: {len(files)}

هل تريد المتابعة؟
"""

    keyboard = [
        [InlineKeyboardButton("✅ تأكيد", callback_data="batch_confirm")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="batch_cancel")]
    ]

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def batch_confirm_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد وإجراء الرفع الدفعي"""
    query = update.callback_query
    await query.answer()

    if query.data == "batch_cancel":
        await query.edit_message_text("❌ تم الإلغاء.")
        context.user_data.pop("batch_files", None)
        context.user_data.pop("batch_mode", None)
        return ConversationHandler.END

    db: Session = context.bot_data.get("db_session")
    files = context.user_data.get("batch_files", [])
    category_id = context.user_data.get("batch_category_id")
    author_id = context.user_data.get("batch_author_id")

    ai_service = get_ai_service()
    added = 0
    failed = 0

    await query.edit_message_text("⏳ جاري رفع الكتب...")

    for file_info in files:
        try:
            # توليد وصف AI
            ai_desc = await ai_service.generate_book_description(
                title=file_info["title"],
                author="",
                category=""
            )

            book = Book(
                title=file_info["title"],
                description=ai_desc or "",
                ai_description=ai_desc or "",
                author_id=author_id,
                category_id=category_id,
                file_id=file_info["file_id"],
                file_size=file_info["file_size"],
                file_type="pdf"
            )

            db.add(book)
            added += 1
        except Exception as e:
            logger.error(f"Batch upload error: {e}")
            failed += 1

    db.commit()

    await context.bot.send_message(
        update.effective_user.id,
        f"✅ تم الانتهاء!
"
        f"📚 نجح: {added}
"
        f"❌ فشل: {failed}"
    )

    # تنظيف
    context.user_data.pop("batch_files", None)
    context.user_data.pop("batch_mode", None)
    context.user_data.pop("batch_category_id", None)
    context.user_data.pop("batch_author_id", None)

    return ConversationHandler.END
