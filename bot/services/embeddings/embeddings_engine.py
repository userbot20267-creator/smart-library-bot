"""محرك التمثيل الدلالي (Embeddings Engine)"""
import logging
import json
from typing import List, Dict, Optional, Any
import numpy as np
from bot.services.ai_service import get_ai_service  # ✅ تم التصحيح

logger = logging.getLogger(__name__)


class EmbeddingsEngine:
    """محرك لتحويل النصوص إلى متجهات رقمية"""

    def __init__(self):
        self.ai_service = get_ai_service()
        self.vector_store: Dict[str, Dict[str, Any]] = {}

    async def create_book_embedding(self, book_id: int, title: str, description: str = "", 
                                     author_name: str = "", category_name: str = "") -> Optional[List[float]]:
        """إنشاء embedding لكتاب"""
        text = f"{title}. {description}. {author_name}. {category_name}"
        embedding = await self.ai_service.generate_embedding_text(text)

        if embedding:
            self.vector_store[f"book_{book_id}"] = {
                "embedding": embedding,
                "metadata": {
                    "book_id": book_id,
                    "title": title,
                    "author": author_name,
                    "category": category_name
                }
            }
        return embedding

    async def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """البحث عن متشابهات"""
        query_embedding = await self.ai_service.generate_embedding_text(query)
        if not query_embedding:
            return []

        query_vector = np.array(query_embedding)
        results = []

        for key, data in self.vector_store.items():
            if key.startswith("book_"):
                book_vector = np.array(data["embedding"])
                similarity = self._cosine_similarity(query_vector, book_vector)
                results.append({
                    "book_id": data["metadata"]["book_id"],
                    "title": data["metadata"]["title"],
                    "similarity": float(similarity)
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """حساب التشابه الكوسيني"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def save_to_file(self, filepath: str):
        """حفظ المتجهات إلى ملف"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.vector_store, f)

    def load_from_file(self, filepath: str):
        """تحميل المتجهات من ملف"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.vector_store = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Vector store file not found: {filepath}")


_embeddings_engine: Optional[EmbeddingsEngine] = None


def get_embeddings_engine() -> EmbeddingsEngine:
    """الحصول على محرك التمثيل الدلالي"""
    global _embeddings_engine
    if _embeddings_engine is None:
        _embeddings_engine = EmbeddingsEngine()
    return _embeddings_engine
