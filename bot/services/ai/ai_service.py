"""خدمة الذكاء الاصطناعي - Microservice"""
import logging
import httpx
from typing import Optional, List, Dict, Any
from bot.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AIService:
    """خدمة AI مستقلة"""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.AI_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://smart-library-bot.com",
            "X-Title": "Smart Library Bot"
        }

    async def _call_api(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
        """استدعاء API"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": 2000
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"AI API error: {e}")
            return None

    async def summarize_text(self, text: str, max_length: int = 500) -> Optional[str]:
        """تلخيص نص"""
        prompt = f"""قم بتلخيص النص التالي بشكل موجز وشامل باللغة العربية.
        اجعل التلخيص لا يتجاوز {max_length} كلمة تقريباً.
        ركز على الأفكار الرئيسية والنقاط المهمة.

        النص:
        {text[:8000]}
        """

        messages = [
            {"role": "system", "content": "أنت مساعد ذكي متخصص في تلخيص الكتب والنصوص باللغة العربية."},
            {"role": "user", "content": prompt}
        ]

        return await self._call_api(messages, temperature=0.5)

    async def generate_book_description(self, title: str, author: str, category: str = "") -> Optional[str]:
        """توليد وصف كتاب"""
        prompt = f"""اكتب وصفاً جذاباً ومختصراً (3-4 أسطر) للكتاب التالي باللغة العربية:

        العنوان: {title}
        المؤلف: {author}
        {f"التصنيف: {category}" if category else ""}

        اجعل الوصف مشوقاً ويحفز على القراءة.
        """

        messages = [
            {"role": "system", "content": "أنت مساعد ذكي متخصص في كتابة أوصاف الكتب باللغة العربية."},
            {"role": "user", "content": prompt}
        ]

        return await self._call_api(messages, temperature=0.8)

    async def suggest_category(self, title: str, author: str, description: str = "") -> Optional[str]:
        """اقتراح قسم للكتاب"""
        prompt = f"""اقترح التصنيف الأنسب للكتاب التالي من هذه التصنيفات الشائعة:
        روايات، علم نفس، تطوير ذات، برمجة، تاريخ، فلسفة، دين، علوم، أدب، سيرة ذاتية، أعمال، صحة، تعليم، فن، غير مصنف

        العنوان: {title}
        المؤلف: {author}
        {f"الوصف: {description}" if description else ""}

        أجب باسم التصنيف فقط بدون أي شرح إضافي.
        """

        messages = [
            {"role": "user", "content": prompt}
        ]

        return await self._call_api(messages, temperature=0.3)

    async def analyze_library(self, books_data: List[Dict[str, Any]]) -> Optional[str]:
        """تحليل المكتبة"""
        prompt = f"""حلل البيانات التالية للمكتبة وقدم تقريراً شاملاً باللغة العربية:

        {books_data}

        قم بتضمين:
        1. نقاط القوة في المكتبة
        2. نقاط الضعف والنواقص
        3. اقتراحات لكتب جديدة
        4. توصيات لتحسين المكتبة
        """

        messages = [
            {"role": "system", "content": "أنت محلل مكتبات ذكي متخصص في تقييم المحتوى الرقمي."},
            {"role": "user", "content": prompt}
        ]

        return await self._call_api(messages, temperature=0.7)

    async def answer_book_question(self, book_text: str, question: str) -> Optional[str]:
        """الإجابة على سؤال حول الكتاب"""
        prompt = f"""بناءً على النص التالي من الكتاب، أجب على السؤال بدقة:

        النص:
        {book_text[:6000]}

        السؤال: {question}

        اجب باللغة العربية بشكل واضح ومفصل.
        """

        messages = [
            {"role": "system", "content": "أنت مساعد أكاديمي متخصص في تحليل وشرح الكتب."},
            {"role": "user", "content": prompt}
        ]

        return await self._call_api(messages, temperature=0.6)

    async def generate_embedding_text(self, text: str) -> Optional[List[float]]:
        """توليد embedding للنص"""
        # يمكن استخدام OpenRouter أو خدمة embeddings محلية
        # للتبسيط، نستخدم نموذج محلي عبر sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(settings.EMBEDDINGS_MODEL)
            embedding = model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None


# Singleton
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """الحصول على خدمة AI"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
