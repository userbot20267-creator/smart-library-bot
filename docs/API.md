# 📡 توثيق API وخدمات البوت

## 🤖 خدمة الذكاء الاصطناعي (AI Service)

### الفئة: `AIService`

#### `summarize_text(text: str, max_length: int = 500) -> Optional[str]`
تلخيص نص باستخدام Google Gemini عبر OpenRouter.

**المعاملات:**
- `text`: النص المراد تلخيصه
- `max_length`: الحد الأقصى للكلمات

**الاستخدام:**
```python
from bot.services import get_ai_service

ai = get_ai_service()
summary = await ai.summarize_text("نص طويل هنا...", max_length=300)
```

#### `generate_book_description(title: str, author: str, category: str = "") -> Optional[str]`
توليد وصف جذاب للكتاب.

**المعاملات:**
- `title`: عنوان الكتاب
- `author`: اسم المؤلف
- `category`: التصنيف (اختياري)

#### `suggest_category(title: str, author: str, description: str = "") -> Optional[str]`
اقتراح تصنيف مناسب للكتاب.

#### `analyze_library(books_data: List[Dict]) -> Optional[str]`
تحليل شامل للمكتبة وإنشاء تقرير.

#### `answer_book_question(book_text: str, question: str) -> Optional[str]`
الإجابة على أسئلة حول محتوى الكتاب.

## 🔍 البحث الدلالي (Semantic Search)

### الفئة: `SemanticSearchEngine`

#### `index_book(book: Book, db: Session) -> bool`
فهرسة كتاب جديد في محرك البحث.

#### `search(query: str, db: Session, top_k: int = 10) -> List[Dict]`
البحث الدلالي عن كتب.

**الاستخدام:**
```python
from bot.services import get_search_engine

engine = get_search_engine()
results = await engine.search("كتب عن التطور البشري", db)
# قد يعيد كتباً عن "النشوء والارتقاء" حتى بدون كلمة "تطور"
```

#### `find_similar_books(book_id: int, db: Session, top_k: int = 5) -> List[Dict]`
البحث عن كتب مشابهة.

## 🧬 محرك التمثيل الدلالي (Embeddings Engine)

### الفئة: `EmbeddingsEngine`

#### `create_book_embedding(book_id, title, description, author_name, category_name) -> Optional[List[float]]`
إنشاء متجه رقمي للكتاب.

#### `search_similar(query: str, top_k: int = 5) -> List[Dict]`
البحث عن كتب متشابهة دلالياً.

## 📊 قاعدة البيانات

### النماذج الرئيسية

#### `User`
| الحقل | النوع | الوصف |
|-------|-------|-------|
| telegram_id | BigInteger | معرف تليجرام |
| username | String | اسم المستخدم |
| total_points | Integer | النقاط |
| is_banned | Boolean | محظور؟ |
| is_admin | Boolean | مشرف؟ |

#### `Book`
| الحقل | النوع | الوصف |
|-------|-------|-------|
| title | String | العنوان |
| description | Text | الوصف |
| file_id | String | معرف ملف تليجرام |
| ai_summary | Text | تلخيص AI |
| embedding_id | String | معرف المتجه |

#### `Category`
| الحقل | النوع | الوصف |
|-------|-------|-------|
| name | String | اسم القسم |
| parent_id | Integer | القسم الأب |

#### `Comment`
| الحقل | النوع | الوصف |
|-------|-------|-------|
| user_id | BigInteger | صاحب التعليق |
| book_id | Integer | الكتاب |
| content | Text | المحتوى |

## 🔐 المصادقة

### `AuthMiddleware`

#### `is_owner(user_id: int) -> bool`
التحقق مما إذا كان المستخدم هو المالك.

#### `is_admin(user: User) -> bool`
التحقق مما إذا كان المستخدم مشرفاً.

## ⏰ الجدولة

### المهام المتاحة

| المهمة | التوقيت | الوصف |
|--------|---------|-------|
| `daily_backup` | كل يوم 3:00 ص | نسخ احتياطي |
| `weekly_report` | كل أحد 9:00 ص | تقرير أسبوعي |
| `rating_reminders` | كل يوم 6:00 م | تذكيرات التقييم |
