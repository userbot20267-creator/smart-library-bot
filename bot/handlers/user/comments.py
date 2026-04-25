"""معالج التعليقات"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationTypes
from sqlalchemy.orm import Session
from bot.database.models import Book, Comment, CommentLike
from bot.keyboards import InlineKeyboards

logger = logging.getLogger(__name__)

# حالات المحادثة
COMMENT_TEXT = 1


async def show_comments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض تعليقات الكتاب"""
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.split("_")[1])
    db: Session = context.bot_data.get("db_session")

    if not db:
        return

    comments = db.query(Comment).filter(Comment.book_id == book_id).order_by(Comment.created_at.desc()).all()

    if not comments:
        await query.edit_message_text(
            "💬 لا توجد تعليقات بعد. كن أول من يعلق!",
            reply_markup=InlineKeyboards.comments_list([], book_id)
        )
        return

    context.user_data["current_book"] = book_id

    await query.edit_message_text(
        f"💬 تعليقات الكتاب ({len(comments)}):",
        reply_markup=InlineKeyboards.comments_list(comments, book_id)
    )


async def add_comment_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء إضافة تعليق"""
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.split("_")[2])
    context.user_data["commenting_book"] = book_id

    await query.edit_message_text(
        "💬 أرسل تعليقك (حتى 200 حرف):

"
        "أو اضغط /cancel للإلغاء."
    )
    return COMMENT_TEXT


async def save_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ التعليق"""
    text = update.message.text
    db: Session = context.bot_data.get("db_session")
    user = update.effective_user
    book_id = context.user_data.get("commenting_book")

    if not db or not book_id:
        await update.message.reply_text("❌ خطأ")
        return ConversationHandler.END

    if len(text) > 200:
        await update.message.reply_text("❌ التعليق طويل جداً. الحد الأقصى 200 حرف.")
        return COMMENT_TEXT

    comment = Comment(
        user_id=user.id,
        book_id=book_id,
        content=text
    )
    db.add(comment)
    db.commit()

    # إضافة نقاط
    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    if db_user:
        db_user.total_points += 2
        db.commit()

    await update.message.reply_text("✅ تم إضافة تعليقك!")

    # عرض التعليقات
    comments = db.query(Comment).filter(Comment.book_id == book_id).order_by(Comment.created_at.desc()).all()
    await update.message.reply_text(
        "💬 التعليقات:",
        reply_markup=InlineKeyboards.comments_list(comments, book_id)
    )

    return ConversationHandler.END


async def like_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الإعجاب بتعليق"""
    query = update.callback_query
    await query.answer()

    comment_id = int(query.data.split("_")[2])
    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    existing = db.query(CommentLike).filter(
        CommentLike.user_id == user.id,
        CommentLike.comment_id == comment_id
    ).first()

    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        return

    if existing:
        db.delete(existing)
        await query.answer("💔 تم إلغاء الإعجاب")
    else:
        like = CommentLike(user_id=user.id, comment_id=comment_id)
        db.add(like)
        await query.answer("❤️ تم الإعجاب!")

    db.commit()

    # تحديث العرض
    comments = db.query(Comment).filter(Comment.book_id == comment.book_id).order_by(Comment.created_at.desc()).all()
    await query.edit_message_text(
        "💬 التعليقات:",
        reply_markup=InlineKeyboards.comments_list(comments, comment.book_id)
    )
