"""نماذج قاعدة البيانات"""
from .base import Base, Database
from .user import User
from .category import Category
from .author import Author
from .book import Book
from .download import Download
from .favorite import Favorite
from .rating import Rating
from .comment import Comment, CommentLike
from .referral import Referral
from .pack import Pack, PackItem
from .notification import Notification
from .required_channel import RequiredChannel

__all__ = [
    "Base", "Database",
    "User", "Category", "Author", "Book",
    "Download", "Favorite", "Rating",
    "Comment", "CommentLike",
    "Referral", "Pack", "PackItem",
    "Notification", "RequiredChannel"
]
