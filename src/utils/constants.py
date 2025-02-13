"""
קבועים למערכת
"""

class QuestionIntent:
    """סוגי כוונות אפשריות בשאלות"""
    SALES_IMPROVEMENT = "שיפור_מכירות"
    MARKETING = "שיווק_ופרסום"
    PRODUCT_MANAGEMENT = "ניהול_מוצרים"
    CUSTOMER_SERVICE = "שירות_לקוחות"
    TECHNICAL = "תמיכה_טכנית"
    ANALYTICS = "נתונים_וניתוח"
    GENERAL = "שאלה_כללית"

class QuestionCategory:
    """קטגוריות שאלות אפשריות"""
    SALES = "מכירות"
    MARKETING = "שיווק"
    PRODUCTS = "מוצרים"
    CUSTOMERS = "לקוחות"
    TECHNICAL = "טכני"
    ANALYTICS = "אנליטיקס"
    GENERAL = "כללי"

# מילות מפתח לכל קטגוריה
CATEGORY_KEYWORDS = {
    QuestionCategory.SALES: [
        'מכירות', 'הכנסות', 'רווח', 'המרה', 'עסקאות', 'מחזור', 
        'הזמנות', 'קופון', 'מבצע', 'הנחה'
    ],
    QuestionCategory.MARKETING: [
        'שיווק', 'פרסום', 'קידום', 'מודעות', 'קמפיין', 'סושיאל',
        'פייסבוק', 'אינסטגרם', 'ניוזלטר', 'אימייל'
    ],
    QuestionCategory.PRODUCTS: [
        'מוצר', 'פריט', 'מלאי', 'קטלוג', 'מחיר', 'הזמנה', 
        'ספק', 'מחסן', 'וריאציות', 'מפרט'
    ],
    QuestionCategory.CUSTOMERS: [
        'לקוח', 'שירות', 'תמיכה', 'פניה', 'תלונה', 'משוב',
        'החזרה', 'זיכוי', 'סטטוס', 'משלוח'
    ],
    QuestionCategory.TECHNICAL: [
        'התקנה', 'הגדרות', 'תקלה', 'באג', 'שגיאה', 'עדכון',
        'גיבוי', 'אבטחה', 'הרשאות', 'חיבור'
    ],
    QuestionCategory.ANALYTICS: [
        'נתונים', 'דוח', 'סטטיסטיקה', 'ניתוח', 'מגמות', 'ביצועים',
        'גרף', 'השוואה', 'תקופה', 'אנליטיקס'
    ]
} 