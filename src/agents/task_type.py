from enum import Enum, auto
from typing import Dict, List, Optional, Any

class TaskType(Enum):
    """סוגי משימות אפשריים"""
    GENERAL_QUESTION = auto()  # שאלה כללית
    PRODUCT_INFO = auto()      # מידע על מוצר
    ORDER_STATUS = auto()      # סטטוס הזמנה
    SALES_REPORT = auto()      # דוח מכירות
    STORE_ADVICE = auto()      # ייעוץ לחנות
    MARKETING = auto()         # שיווק ופרסום
    INVENTORY = auto()         # ניהול מלאי
    CUSTOMER_SERVICE = auto()  # שירות לקוחות
    TECHNICAL = auto()         # תמיכה טכנית
    ERROR = auto()             # שגיאה בזיהוי המשימה

    @staticmethod
    def identify_task(message: str, context: Optional[Dict[str, Any]] = None) -> 'TaskType':
        """
        זיהוי סוג המשימה לפי תוכן ההודעה והקשר השיחה
        
        Args:
            message: תוכן ההודעה
            context: הקשר השיחה (אופציונלי)
            
        Returns:
            TaskType: סוג המשימה המזוהה
        """
        message_lower = message.lower()
        
        # מילות מפתח לכל סוג משימה
        keywords = {
            TaskType.PRODUCT_INFO: [
                "מוצר", "פריט", "מחיר", "קטלוג", "מפרט", "תמונה", "תיאור",
                "זמין", "במלאי", "וריאציות", "מידות", "צבעים"
            ],
            TaskType.ORDER_STATUS: [
                "הזמנה", "משלוח", "סטטוס", "מעקב", "איסוף", "החזרה", "ביטול",
                "מספר הזמנה", "תאריך", "כתובת", "אספקה", "שליח"
            ],
            TaskType.SALES_REPORT: [
                "מכירות", "דוח", "הכנסות", "רווח", "סטטיסטיקה", "נתונים",
                "מגמות", "ביצועים", "תקופה", "השוואה", "גרף", "אנליטיקס"
            ],
            TaskType.MARKETING: [
                "שיווק", "פרסום", "קמפיין", "קידום", "מבצע", "הנחה",
                "סושיאל", "פייסבוק", "אינסטגרם", "מייל", "ניוזלטר"
            ],
            TaskType.INVENTORY: [
                "מלאי", "כמות", "הזמנה מספק", "מחסן", "ספירה", "מינימום",
                "מקסימום", "התראה", "חוסר", "עודף", "תנועות"
            ],
            TaskType.CUSTOMER_SERVICE: [
                "לקוח", "תלונה", "פנייה", "שירות", "תמיכה", "החזר",
                "זיכוי", "שאלה", "בעיה", "עזרה", "צאט"
            ],
            TaskType.TECHNICAL: [
                "תקלה", "באג", "שגיאה", "התקנה", "עדכון", "גיבוי",
                "אבטחה", "הגדרות", "חיבור", "ממשק", "אפליקציה"
            ],
            TaskType.STORE_ADVICE: [
                "המלצה", "ייעוץ", "שיפור", "אופטימיזציה", "אסטרטגיה",
                "תכנון", "פיתוח", "גדילה", "מתחרים", "שוק"
            ]
        }
        
        # בדיקת הקשר קודם אם קיים
        if context and 'last_task_type' in context:
            # אם ההודעה קצרה ונראית כהמשך שיחה
            if len(message_lower.split()) <= 3 and not any(
                any(kw in message_lower for kw in task_keywords)
                for task_keywords in keywords.values()
            ):
                return context['last_task_type']
        
        # חיפוש מילות מפתח בהודעה
        max_matches = 0
        identified_task = TaskType.GENERAL_QUESTION
        
        for task_type, task_keywords in keywords.items():
            matches = sum(1 for kw in task_keywords if kw in message_lower)
            if matches > max_matches:
                max_matches = matches
                identified_task = task_type
        
        return identified_task

    @staticmethod
    def get_prompt_params(task_type: 'TaskType') -> Dict[str, Any]:
        """
        מחזיר פרמטרים מותאמים לפי סוג המשימה
        """
        base_params = {
            "model": "deepseek-chat",
            "temperature": 0.3,
            "max_tokens": 500,
            "top_p": 0.9
        }

        # התאמת פרמטרים לפי סוג המשימה
        params_by_type = {
            TaskType.GENERAL_QUESTION: {"temperature": 0.3},
            TaskType.PRODUCT_INFO: {"temperature": 0.2},
            TaskType.ORDER_STATUS: {"temperature": 0.1},
            TaskType.SALES_REPORT: {"temperature": 0.2},
            TaskType.MARKETING: {"temperature": 0.3},
            TaskType.INVENTORY: {"temperature": 0.2},
            TaskType.CUSTOMER_SERVICE: {"temperature": 0.4},
            TaskType.TECHNICAL: {"temperature": 0.2},
            TaskType.STORE_ADVICE: {"temperature": 0.3},
            TaskType.ERROR: {"temperature": 0.1}
        }

        if task_type in params_by_type:
            base_params.update(params_by_type[task_type])

        return base_params 