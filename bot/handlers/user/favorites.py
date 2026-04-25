"""معالج المفضلة"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import Favorite, Book
from bot.keyboards import InlineKeyboards

logger = logging.getLogger(__name__)


async def my_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المفضلة"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    favorites = db.query(Favorite).filter(Favorite.user_id == user.id).all()

    if not favorites:
        await query.edit_message_text(
            "❤️ قائمة المفضلة فارغة.\nأضف كتباً من المكتبة!",
            reply_markup=InlineKeyboards.main_menu()
        )
        return

    books = [f.book for f in favorites]
    context.user_data["books_list"] = books

    await query.edit_message_text(
        f"❤️ مفضلتك ({len(books)} كتاب):",
        reply_markup=InlineKeyboards.books_list(books)
    )


async def my_downloads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض سجل التحميلات"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    from bot.database.models import Download
    downloads = db.query(Download).filter(Download.user_id == user.id).order_by(Download.downloaded_at.desc()).all()

    if not downloads:
        await query.edit_message_text(
            "📜 لم تقم بتحميل أي كتب بعد.",
            reply_markup=InlineKeyboards.main_menu()
        )
        return

    text = "📜 <b>سجل التحميلات</b>\n\n"
    for i, dl in enumerate(downloads[:20], 1):
        book_title = dl.book.title if dl.book else "غير معروف"
        date = dl.downloaded_at.strftime("%Y-%m-%d") if dl.downloaded_at else "غير معروف"
        text += f"{i}. 📖 {book_title} - {date}\n"

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboards.main_menu())
    
