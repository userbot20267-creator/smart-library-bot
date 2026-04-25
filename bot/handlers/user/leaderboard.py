"""معالج لوحة الشرف"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import User
from bot.keyboards import InlineKeyboards
from bot.utils import get_badge

logger = logging.getLogger(__name__)


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض لوحة الشرف"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")

    if not db:
        return

    top_users = db.query(User).filter(User.is_banned == False).order_by(User.total_points.desc()).limit(10).all()

    if not top_users:
        await query.edit_message_text(
            "🏆 لا يوجد مستخدمين مسجلين بعد.",
            reply_markup=InlineKeyboards.main_menu()
        )
        return

    # تم استخدام \n للنزول لسطر جديد بدلاً من كسر النص برمجياً
    text = "🏆 <b>لوحة الشرف</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, user in enumerate(top_users):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        badge = get_badge(user.total_points)
        name = user.first_name or f"مستخدم {user.telegram_id}"
        text += f"{medal} {name} - {user.total_points} نقطة {badge}\n"

    # إضافة ترتيب المستخدم الحالي
    current_user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
    if current_user:
        all_users = db.query(User).filter(User.is_banned == False).order_by(User.total_points.desc()).all()
        try:
            rank = [u.id for u in all_users].index(current_user.id) + 1
            text += f"\n📊 ترتيبك: #{rank} | نقاطك: {current_user.total_points}"
        except ValueError:
            pass

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboards.main_menu())
    
