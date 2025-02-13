"""
מבני נתונים למאגר שאלות ותשובות
"""

from dataclasses import dataclass
from typing import List, Optional
from .constants import QuestionCategory, QuestionIntent

@dataclass
class FAQEntry:
    """מבנה נתונים לשאלה נפוצה"""
    question: str
    answer: str
    category: str
    keywords: List[str]
    intent: str
    examples: List[str]
    embedding: Optional[List[float]] = None

# שאלות ותשובות בסיסיות
INITIAL_FAQS = [
    FAQEntry(
        question="איך אני יכול לשפר את אחוזי ההמרה?",
        answer="""
        הנה מספר דרכים אפקטיביות לשיפור אחוזי ההמרה בחנות שלך:

        1. שיפור חווית המשתמש:
           • פישוט תהליך הרכישה
           • שיפור מהירות האתר
           • התאמה למובייל

        2. אופטימיזציה של דפי מוצר:
           • תמונות איכותיות
           • תיאורים מפורטים
           • ביקורות לקוחות

        3. בניית אמון:
           • תעודות אבטחה
           • מדיניות החזרה ברורה
           • פרטי קשר נגישים

        💡 טיפ: התחל במדידת אחוזי ההמרה הנוכחיים כדי לעקוב אחר השיפור.

        רוצה שנצלול לעומק לאחד התחומים? 🤔
        """,
        category=QuestionCategory.SALES,
        keywords=['המרה', 'שיפור', 'מכירות', 'אופטימיזציה'],
        intent=QuestionIntent.SALES_IMPROVEMENT,
        examples=[
            "איך להגדיל את אחוזי ההמרה?",
            "איך לשפר את שיעור ההמרה?",
            "מה יעזור להמיר יותר גולשים?"
        ]
    ),
    FAQEntry(
        question="איך אני יכול לשפר את המכירות?",
        answer="""
        אשמח לעזור לך לשפר את המכירות! 📈

        הנה אסטרטגיה מקיפה:

        1. שיווק ממוקד:
           • קמפיינים בפייסבוק/אינסטגרם
           • שיווק באימייל
           • קידום אורגני

        2. שיפור חווית הקנייה:
           • ממשק משתמש נוח
           • תהליך תשלום פשוט
           • שירות לקוחות מעולה

        3. אופטימיזציה של מוצרים:
           • מחירים תחרותיים
           • מבצעים אטרקטיביים
           • צילומים מקצועיים

        💡 טיפ: התמקד קודם בלקוחות הקיימים - זה יכול להגדיל מכירות ב-25%!

        רוצה לדעת עוד על אחד התחומים? 😊
        """,
        category=QuestionCategory.SALES,
        keywords=['מכירות', 'שיפור', 'הכנסות', 'צמיחה'],
        intent=QuestionIntent.SALES_IMPROVEMENT,
        examples=[
            "איך להגדיל את המכירות?",
            "איך למכור יותר?",
            "דרכים להגדלת מכירות"
        ]
    ),
    FAQEntry(
        question="איך לנהל מלאי בצורה יעילה?",
        answer="""
        ניהול מלאי יעיל הוא קריטי להצלחת החנות! 📦

        הנה המלצות מעשיות:

        1. מעקב ובקרה:
           • הגדרת מלאי מינימום לכל מוצר
           • התראות אוטומטיות על מלאי נמוך
           • מעקב אחר מוצרים איטיים

        2. תכנון מלאי:
           • חיזוי ביקושים לפי עונות
           • ניהול הזמנות מספקים
           • אופטימיזציה של רמות מלאי

        3. שימוש בכלים:
           • מערכת ניהול מלאי
           • סריקת ברקודים
           • דוחות תנועות מלאי

        💡 טיפ: בצע ספירות מלאי תקופתיות לוודא דיוק.

        צריך עזרה בהטמעת אחת השיטות? 🤔
        """,
        category=QuestionCategory.PRODUCTS,
        keywords=['מלאי', 'ניהול', 'מוצרים', 'ספקים'],
        intent=QuestionIntent.PRODUCT_MANAGEMENT,
        examples=[
            "איך לנהל את המלאי?",
            "מה הדרך הטובה לנהל מלאי?",
            "טיפים לניהול מלאי"
        ]
    ),
    FAQEntry(
        question="איך לשפר את שירות הלקוחות?",
        answer="""
        שירות לקוחות מעולה = לקוחות נאמנים! 🤝

        הנה תכנית פעולה:

        1. זמינות ומענה:
           • זמני תגובה מהירים
           • מגוון ערוצי תקשורת
           • מענה אישי ומקצועי

        2. מדיניות ברורה:
           • תנאי החזרה והחלפה
           • מדיניות משלוחים
           • טיפול בתלונות

        3. מעקב ושיפור:
           • משוב מלקוחות
           • מדידת שביעות רצון
           • למידה מתלונות

        💡 טיפ: צור מאגר תשובות לשאלות נפוצות.

        רוצה לדעת איך ליישם אחד מהתחומים? 😊
        """,
        category=QuestionCategory.CUSTOMERS,
        keywords=['שירות', 'לקוחות', 'תמיכה', 'מענה'],
        intent=QuestionIntent.CUSTOMER_SERVICE,
        examples=[
            "איך לתת שירות טוב יותר?",
            "איך לשפר את חווית הלקוח?",
            "טיפים לשירות לקוחות"
        ]
    ),
    FAQEntry(
        question="איך לנתח את ביצועי החנות?",
        answer="""
        ניתוח נתונים חכם = החלטות טובות יותר! 📊

        הנה המדדים החשובים:

        1. מדדי מכירות:
           • הכנסות יומיות/חודשיות
           • ערך הזמנה ממוצע
           • שיעורי המרה

        2. התנהגות לקוחות:
           • דפוסי רכישה
           • נטישת עגלות
           • זמן באתר

        3. מדדי מוצרים:
           • מוצרים מובילים
           • שולי רווח
           • מלאי מתגלגל

        💡 טיפ: הגדר יעדים מדידים לכל מדד.

        רוצה לצלול לעומק אחד המדדים? 📈
        """,
        category=QuestionCategory.ANALYTICS,
        keywords=['ניתוח', 'ביצועים', 'מדדים', 'דוחות'],
        intent=QuestionIntent.ANALYTICS,
        examples=[
            "איך לבדוק את ביצועי החנות?",
            "אילו מדדים חשוב לעקוב?",
            "איך לנתח נתונים בחנות?"
        ]
    )
] 