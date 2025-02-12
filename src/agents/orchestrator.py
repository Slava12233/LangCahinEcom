"""
Orchestrator agent that coordinates between user requests and various specialized agents.
"""

import json
from typing import Dict, Any, Optional
import requests
import time
from dataclasses import dataclass
from datetime import datetime
from utils import get_logger
from utils.cache_manager import SimpleCache

# יצירת לוגר ייעודי ל-Orchestrator
logger = get_logger(__name__)

@dataclass
class PerformanceMetrics:
    """מחלקה לשמירת מדדי ביצועים"""
    total_time: float = 0.0
    cache_lookup_time: float = 0.0
    api_call_time: float = 0.0
    cache_hit: bool = False
    attempt_count: int = 0
    response_length: int = 0
    task_type: str = ""
    timestamp: datetime = datetime.now()

class TaskType:
    """סוגי משימות אפשריים"""
    PRODUCT_INFO = "product_info"
    ORDER_STATUS = "order_status"
    SALES_REPORT = "sales_report"
    CUSTOMER_SERVICE = "customer_service"
    GENERAL_QUERY = "general_query"

    @staticmethod
    def get_prompt_params(task_type: str) -> Dict[str, Any]:
        """פרמטרים מותאמים למודל לפי סוג המשימה"""
        base_params = {
            "model": "deepseek-chat",
            "temperature": 0.3,
            "max_tokens": 200,
            "top_p": 0.9,
            "presence_penalty": 0.1
        }
        
        task_params = {
            TaskType.PRODUCT_INFO: {"temperature": 0.2, "max_tokens": 150},
            TaskType.ORDER_STATUS: {"temperature": 0.1, "max_tokens": 100},
            TaskType.SALES_REPORT: {"temperature": 0.4, "max_tokens": 250},
            TaskType.CUSTOMER_SERVICE: {"temperature": 0.5, "max_tokens": 200},
            TaskType.GENERAL_QUERY: {"temperature": 0.3, "max_tokens": 150}
        }
        
        return {**base_params, **task_params.get(task_type, {})}

class OrchestratorAgent:
    def __init__(self, deepseek_api_key: str):
        """Initialize the orchestrator with necessary components."""
        self.api_key = deepseek_api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.conversation_history = []
        self.max_retries = 5
        self.timeout = 30
        
        # יצירת מטמון פשוט
        self.cache = SimpleCache(ttl=3600, maxsize=1000)
        
        # מטמון למדדי ביצועים
        self.performance_metrics = []
        
        # הגדרת פרומפט בסיסי למערכת
        self.base_system_prompt = """אני עוזר חכם לניהול חנות אונליין 🏪

תפקידי:
1. לספק מידע מקצועי על ניהול חנות אונליין
2. לתת המלצות וטיפים מעשיים לשיפור המכירות
3. לענות על שאלות בנושאי:
   • ניהול מוצרים ומלאי
   • שיווק ופרסום
   • שירות לקוחות
   • אופטימיזציה וביצועים
   • מגמות בשוק

חשוב לציין:
- אני אתן תשובות מקצועיות ומעשיות
- אם נשאל על נתונים ספציפיים מהחנות, אציין שזה עדיין לא זמין
- אתמקד במתן ערך גם בלי גישה למידע בזמן אמת

ענה בצורה:
✓ מקצועית ומדויקת
✓ ידידותית ומובנת
✓ עם דוגמאות מעשיות
✓ עם אימוג'ים מתאימים"""

        logger.info(
            "מאתחל את ה-Orchestrator",
            extra={
                "api_url": self.api_url,
                "api_key_length": len(self.api_key) if self.api_key else 0,
                "timeout": self.timeout,
                "max_retries": self.max_retries,
                "cache_ttl": 3600,
                "cache_maxsize": 1000
            }
        )
        
        # הגדרת פרומפטים לפי סוג משימה
        self.task_prompts = {
            TaskType.PRODUCT_INFO: """עוזר חנות חכם 🏪
תפקידך:
• מידע על מוצרים 📦
• מחירים ומלאי 💰
• המלצות קנייה 🛍️

ענה בצורה ידידותית וברורה עם אימוג'ים מתאימים.""",

            TaskType.ORDER_STATUS: """עוזר חנות חכם 🏪
תפקידך:
• מעקב הזמנות 📦
• סטטוס משלוחים 🚚
• עדכוני זמנים 📅

ענה בצורה מדויקת וברורה עם אימוג'ים מתאימים.""",

            TaskType.SALES_REPORT: """עוזר חנות חכם 🏪
תפקידך:
• ניתוח מכירות 📊
• מגמות והמלצות 📈
• תובנות עסקיות 💡

ענה בצורה מקצועית וברורה עם אימוג'ים מתאימים.""",

            TaskType.CUSTOMER_SERVICE: """עוזר חנות חכם 🏪
תפקידך:
• פתרון בעיות ⚡
• שירות לקוחות 🤝
• תמיכה טכנית 🛠️

ענה בצורה אמפתית וברורה עם אימוג'ים מתאימים.""",

            TaskType.GENERAL_QUERY: """עוזר חנות חכם 🏪

אני כאן לעזור לך בניהול החנות שלך! 

יכולות נוכחיות:
• מתן מידע והסברים על ניהול חנות אונליין 📚
• המלצות לשיפור המכירות והשיווק 💡
• תשובות לשאלות נפוצות בניהול חנות 💬
• טיפים מקצועיים לאופטימיזציה 🎯
• הסברים על מושגים בתחום המסחר האלקטרוני 🌐

בקרוב אוכל גם:
• להציג נתונים בזמן אמת מהחנות 📊
• לבצע פעולות ניהול ישירות 🛠️
• לנתח מגמות ולתת תובנות מבוססות נתונים 📈

אשמח לענות על כל שאלה ולעזור בכל נושא הקשור לניהול החנות שלך!

חשוב לציין: כרגע אני בשלבי פיתוח, ולכן חלק מהיכולות המתקדמות עדיין אינן זמינות. אני אעדכן אותך כשיכולות חדשות יתווספו!

ענה בצורה מקצועית, ידידותית וברורה."""
        }

    def _identify_task_type(self, message: str) -> str:
        """זיהוי פשוט של סוג המשימה לפי מילות מפתח"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["מחיר", "מוצר", "פריט", "קטלוג"]):
            return TaskType.PRODUCT_INFO
        elif any(word in message_lower for word in ["הזמנה", "משלוח", "סטטוס"]):
            return TaskType.ORDER_STATUS
        elif any(word in message_lower for word in ["מכירות", "דוח", "הכנסות"]):
            return TaskType.SALES_REPORT
        elif any(word in message_lower for word in ["בעיה", "תלונה", "שירות"]):
            return TaskType.CUSTOMER_SERVICE
            
        return TaskType.GENERAL_QUERY

    def handle_user_message(self, message: str) -> str:
        """Process user message and return appropriate response."""
        metrics = PerformanceMetrics()
        start_time = time.time()
        
        try:
            # זיהוי סוג המשימה
            task_type = self._identify_task_type(message)
            metrics.task_type = task_type
            
            # הוספת ההודעה להיסטוריה
            self.conversation_history.append({"role": "user", "content": message})
            
            logger.info(
                "מתחיל לטפל בהודעת משתמש חדשה",
                extra={
                    "message_length": len(message),
                    "conversation_history_length": len(self.conversation_history),
                    "task_type": task_type
                }
            )
            
            # בדיקה במטמון
            cache_start = time.time()
            cached_response, is_cached = self.cache.get(message)
            metrics.cache_lookup_time = time.time() - cache_start
            
            if cached_response:
                metrics.cache_hit = True
                logger.info(
                    "נמצאה תשובה במטמון",
                    extra={
                        "response_length": len(cached_response),
                        "task_type": task_type
                    }
                )
                metrics.response_length = len(cached_response)
                metrics.total_time = time.time() - start_time
                self.performance_metrics.append(metrics)
                return cached_response

            # בחירת הפרומפט המתאים
            if task_type in [TaskType.PRODUCT_INFO, TaskType.ORDER_STATUS, TaskType.SALES_REPORT]:
                # שאלות שדורשות מידע מהחנות
                system_message = f"""
{self.base_system_prompt}

חשוב: אין לי כרגע גישה למידע בזמן אמת מהחנות.
אני אסביר מה אפשר יהיה לעשות בקרוב ואתן טיפים כלליים בינתיים."""
            else:
                # שאלות כלליות או ייעוץ
                system_message = self.base_system_prompt

            # הכנת הבקשה
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
            
            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
                "stream": False
            }

            # ניסיון עם מספר retries
            for attempt in range(self.max_retries):
                metrics.attempt_count = attempt + 1
                try:
                    logger.debug(
                        f"ניסיון {attempt + 1} מתוך {self.max_retries}",
                        extra={
                            "attempt": attempt + 1,
                            "task_type": task_type,
                            "request_data": {
                                "url": self.api_url,
                                "headers": {**headers, "Authorization": "Bearer [HIDDEN]"},
                                "data": data
                            }
                        }
                    )
                    
                    logger.info(
                        "שולח בקשה ל-DeepSeek API",
                        extra={
                            "attempt": attempt + 1,
                            "task_type": task_type,
                            "request_length": len(str(data)),
                            "request_details": {
                                "model": data["model"],
                                "temperature": data["temperature"],
                                "max_tokens": data["max_tokens"],
                                "messages_count": len(data["messages"]),
                                "system_message_length": len(data["messages"][0]["content"]),
                                "user_message_length": len(data["messages"][1]["content"])
                            }
                        }
                    )
                    
                    api_start = time.time()
                    try:
                        response = requests.post(
                            self.api_url,
                            headers=headers,
                            json=data,
                            timeout=self.timeout
                        )
                        response.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        logger.error(
                            "שגיאה בשליחת הבקשה ל-API",
                            extra={
                                "error": str(e),
                                "status_code": getattr(e.response, 'status_code', None),
                                "response_text": getattr(e.response, 'text', None)
                            }
                        )
                        raise
                    
                    result = response.json()
                    metrics.api_call_time = time.time() - api_start

                    logger.info(
                        "התקבל מענה מה-API",
                        extra={
                            "status_code": response.status_code,
                            "response_time": metrics.api_call_time,
                            "raw_response_length": len(response.text)
                        }
                    )
                    
                    assistant_message = result["choices"][0]["message"]["content"]
                    metrics.response_length = len(assistant_message)
                    
                    logger.info(
                        "התקבלה תשובה מ-DeepSeek API",
                        extra={
                            "response_length": len(assistant_message),
                            "task_type": task_type,
                            "attempt": attempt + 1
                        }
                    )
                    
                    # הוספת התשובה להיסטוריה
                    self.conversation_history.append({"role": "assistant", "content": assistant_message})
                    
                    # שמירה במטמון
                    self.cache.set(message, assistant_message)
                    
                    metrics.total_time = time.time() - start_time
                    self.performance_metrics.append(metrics)
                    
                    return assistant_message
                    
                except requests.Timeout:
                    logger.warning(f"Timeout בניסיון {attempt + 1}")
                    if attempt == self.max_retries - 1:
                        raise
                    time.sleep(1)
                    
                except requests.RequestException as e:
                    logger.error(
                        f"שגיאת רשת בניסיון {attempt + 1}",
                        extra={"error": str(e)}
                    )
                    if attempt == self.max_retries - 1:
                        raise
                    time.sleep(1)

            raise Exception("כל הניסיונות נכשלו")

        except Exception as e:
            logger.error(
                "שגיאה בטיפול בהודעה",
                extra={
                    "error": str(e),
                    "message": message
                }
            )
            metrics.total_time = time.time() - start_time
            self.performance_metrics.append(metrics)
            return "מצטער, נתקלתי בבעיה. אנא נסה שוב או נסח את השאלה אחרת."

    def get_performance_stats(self) -> Dict[str, Any]:
        """מחזיר סטטיסטיקות ביצועים"""
        if not self.performance_metrics:
            return {"error": "אין נתוני ביצועים"}
            
        total_requests = len(self.performance_metrics)
        cache_hits = sum(1 for m in self.performance_metrics if m.cache_hit)
        avg_total_time = sum(m.total_time for m in self.performance_metrics) / total_requests
        avg_api_time = sum(m.api_call_time for m in self.performance_metrics if not m.cache_hit) / (total_requests - cache_hits) if total_requests > cache_hits else 0
        
        # ניתוח לפי סוג משימה
        task_type_stats = {}
        for task_type in set(m.task_type for m in self.performance_metrics):
            task_metrics = [m for m in self.performance_metrics if m.task_type == task_type]
            task_type_stats[task_type] = {
                "count": len(task_metrics),
                "avg_time": sum(m.total_time for m in task_metrics) / len(task_metrics),
                "cache_hits": sum(1 for m in task_metrics if m.cache_hit)
            }
        
        return {
            "total_requests": total_requests,
            "cache_hits": cache_hits,
            "cache_hit_rate": cache_hits / total_requests,
            "avg_total_time": avg_total_time,
            "avg_api_time": avg_api_time,
            "avg_response_length": sum(m.response_length for m in self.performance_metrics) / total_requests,
            "task_type_stats": task_type_stats,
            "cache_stats": self.cache.get_stats()
        } 