"""نظام الباقات (Packs System)"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import Pack, PackItem, Book
from bot.keyboards import InlineKeyboards

logger = logging.getLogger(__name__)


async def browse_packs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تصفح الباقات"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    if not db:
        return

    packs = db.query(Pack).filter(Pack.is_active == True).all()

    if not packs:
        await query.edit_message_text(
            "📦 لا توجد باقات متاحة حالياً.",
            reply_markup=InlineKeyboards.main_menu()
        )
        return

    # تصحيح: دمج النصوص وإضافة رمز السطر الجديد \n
    await query.edit_message_text(
        "📦 <b>الباقات التعليمية</b>\n\n"
        "مسارات منظمة للقراءة:",
        parse_mode="HTML",
        reply_markup=InlineKeyboards.packs_list(packs)
    )


async def show_pack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض محتويات الباقة"""
    query = update.callback_query
    await query.answer()

    pack_id = int(query.data.split("_")[1])
    db: Session = context.bot_data.get("db_session")

    if not db:
        return

    pack = db.query(Pack).filter(Pack.id == pack_id).first()
    if not pack:
        await query.edit_message_text("❌ الباقة غير موجودة")
        return

    items = pack.items

    text = f"""
📦 <b>{pack.name}</b>

{pack.description or ''}

📚 <b>الكتب في هذا المسار ({len(items)}):</b>
"""
    for item in items:
        status = "✅" if item.book.download_count > 0 else "⬜"
        # تصحيح: إضافة \n في بداية السطر لضمان التنسيق
        text += f"\n{status} {item.order}. {item.book.title}"
        if item.notes:
            text += f"\n   💡 {item.notes}"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboards.pack_items(items, pack_id)
    )
