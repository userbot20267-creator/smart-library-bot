"""معالجات المشرف والمالك"""
from .owner import admin_panel, admin_stats, admin_users, broadcast_start, broadcast_send, export_users
from .books_management import (
    admin_books, add_book_start, add_book_title, add_book_author,
    add_book_category, add_book_description, add_book_file,
    list_all_books, advanced_search_books, ai_recategorize
)
from .ai_search import ai_search_command, process_ai_search, confirm_ai_add
from .batch_upload import (
    batch_upload_start, collect_batch_files, batch_done,
    batch_select_category, batch_select_author, batch_confirm_upload
)
from .ai_insights import ai_insights_command, generate_description_for_existing, save_ai_description

__all__ = [
    "admin_panel", "admin_stats", "admin_users", "broadcast_start", "broadcast_send", "export_users",
    "admin_books", "add_book_start", "add_book_title", "add_book_author",
    "add_book_category", "add_book_description", "add_book_file",
    "list_all_books", "advanced_search_books", "ai_recategorize",
    "ai_search_command", "process_ai_search", "confirm_ai_add",
    "batch_upload_start", "collect_batch_files", "batch_done",
    "batch_select_category", "batch_select_author", "batch_confirm_upload",
    "ai_insights_command", "generate_description_for_existing", "save_ai_description"
]
