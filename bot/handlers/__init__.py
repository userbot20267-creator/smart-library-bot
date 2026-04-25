"""المعالجات"""
from .user import *
from .admin import *

__all__ = [
    # User handlers
    "start_command", "profile_command", "referral_command",
    "browse_categories", "show_category_books", "show_book_details",
    "download_book", "toggle_favorite", "rate_book", "share_book",
    "search_command", "process_search", "smart_search_callback",
    "ai_summary", "similar_books", "ai_assistant",
    "show_comments", "add_comment_start", "save_comment", "like_comment",
    "my_favorites", "my_downloads",
    "show_leaderboard",
    # Admin handlers
    "admin_panel", "admin_stats", "admin_users", "broadcast_start", "broadcast_send", "export_users",
    "admin_books", "add_book_start", "add_book_title", "add_book_author",
    "add_book_category", "add_book_description", "add_book_file",
    "list_all_books", "advanced_search_books", "ai_recategorize",
    "ai_search_command", "process_ai_search", "confirm_ai_add",
    "batch_upload_start", "collect_batch_files", "batch_done",
    "batch_select_category", "batch_select_author", "batch_confirm_upload",
    "ai_insights_command", "generate_description_for_existing", "save_ai_description"
]
