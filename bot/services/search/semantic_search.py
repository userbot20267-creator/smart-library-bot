"""البحث الدلالي (Semantic Search)"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from bot.database.models import Book
from bot.services.ai import get_ai_service

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """محرك البحث الدلالي"""

    def __init__(self):
        self.ai_service = get_ai_service()
        self.embeddings_cache: Dict[int, List[float]] = {}

    async def index_book(self, book: Book, db: Session) -> bool:
        """فهرسة كتاب جديد"""
        try:
            # توليد نص للفهرسة
            text_to_index = f"{book.title} {book.description or ''}"
            if book.author:
                text_to_index += f" {book.author.name}"

            embedding = await self.ai_service.generate_embedding_text(text_to_index)
            if embedding:
                self.embeddings_cache[book.id] = embedding
                # يمكن حفظ في قاعدة بيانات متجهات مثل pgvector
                logger.info(f"✅ تم فهرسة الكتاب: {book.title}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error indexing book {book.id}: {e}")
            return False

    async def search(self, query: str, db: Session, top_k: int = 10) -> List[Dict[str, Any]]:
        """بحث دلالي"""
        try:
            # توليد embedding للاستعلام
            query_embedding = await self.ai_service.generate_embedding_text(query)
            if not query_embedding:
                return []

            query_vector = np.array(query_embedding)

            # البحث في الكتب النشطة
            books = db.query(Book).filter(Book.is_active == True).all()

            results = []
            for book in books:
                # فهرسة الكتاب إذا لم يكن مفهرساً
                if book.id not in self.embeddings_cache:
                    await self.index_book(book, db)

                if book.id in self.embeddings_cache:
                    book_vector = np.array(self.embeddings_cache[book.id])
                    similarity = self._cosine_similarity(query_vector, book_vector)

                    results.append({
                        "book": book,
                        "similarity": float(similarity),
                        "score": float(similarity)
                    })

            # ترتيب حسب التشابه
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """حساب التشابه الكوسيني"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    async def find_similar_books(self, book_id: int, db: Session, top_k: int = 5) -> List[Dict[str, Any]]:
        """البحث عن كتب مشابهة"""
        if book_id not in self.embeddings_cache:
            book = db.query(Book).filter(Book.id == book_id).first()
            if book:
                await self.index_book(book, db)

        if book_id not in self.embeddings_cache:
            return []

        book_vector = np.array(self.embeddings_cache[book_id])

        results = []
        books = db.query(Book).filter(Book.id != book_id, Book.is_active == True).all()

        for book in books:
            if book.id in self.embeddings_cache:
                other_vector = np.array(self.embeddings_cache[book.id])
                similarity = self._cosine_similarity(book_vector, other_vector)
                results.append({
                    "book": book,
                    "similarity": float(similarity)
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]


_search_engine: Optional[SemanticSearchEngine] = None


def get_search_engine() -> SemanticSearchEngine:
    """الحصول على محرك البحث"""
    global _search_engine
    if _search_engine is None:
        _search_engine = SemanticSearchEngine()
    return _search_engine
