"""معالجات المستخدم"""
from .start import start_command, profile_command, referral_command
from .books import (
    browse_categories, show_category_books, show_book_details,
    download_book, toggle_favorite, rate_book, share_book
)
from .search import search_command, process_search, smart_search_callback
from .ai_features import ai_summary, similar_books, ai_assistant
from .comments import show_comments, add_comment_start, save_comment, like_comment
from .favorites import my_favorites, my_downloads
from .leaderboard import show_leaderboard

__all__ = [
    "start_command", "profile_command", "referral_command",
    "browse_categories", "show_category_books", "show_book_details",
    "download_book", "toggle_favorite", "rate_book", "share_book",
    "search_command", "process_search", "smart_search_callback",
    "ai_summary", "similar_books", "ai_assistant",
    "show_comments", "add_comment_start", "save_comment", "like_comment",
    "my_favorites", "my_downloads",
    "show_leaderboard"
]
