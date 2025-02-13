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
from utils.embeddings_manager import EmbeddingsManager
import aiohttp
import asyncio

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
            "max_tokens": 500,
            "top_p": 0.9
        }
        
        task_params = {
            TaskType.PRODUCT_INFO: {"temperature": 0.2, "max_tokens": 500},
            TaskType.ORDER_STATUS: {"temperature": 0.1, "max_tokens": 500},
            TaskType.SALES_REPORT: {"temperature": 0.2, "max_tokens": 500},
            TaskType.CUSTOMER_SERVICE: {"temperature": 0.3, "max_tokens": 500},
            TaskType.GENERAL_QUERY: {"temperature": 0.3, "max_tokens": 500}
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
        
        # ניקוי המטמון בהתחלה
        self.cache.clear()
        logger.info("המטמון נוקה בהתחלה")
        
        # מטמון למדדי ביצועים
        self.performance_metrics = []
        
        # יצירת מנהל embeddings
        self.embeddings_manager = EmbeddingsManager()
        
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

    def _create_messages(self, user_message: str) -> list:
        """יצירת רשימת ההודעות לשליחה ל-API"""
        task_type = self._identify_task_type(user_message)
        system_prompt = self.task_prompts.get(task_type, self.base_system_prompt)
        
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history[-5:],  # רק 5 ההודעות האחרונות
            {"role": "user", "content": user_message}
        ]
        
        return messages

    async def handle_user_message(self, message: str, conversation_id: str = None) -> str:
        """Process user message and return appropriate response."""
        metrics = PerformanceMetrics()
        start_time = time.time()
        
        try:
            if not conversation_id:
                logger.warning("לא התקבל מזהה שיחה, משתמש במזהה ברירת מחדל")
                conversation_id = "default"
            
            # בדיקה במטמון
            cache_start = time.time()
            cached_response, is_cached = self.cache.get(message, conversation_id)
            metrics.cache_lookup_time = time.time() - cache_start
            
            if cached_response:
                metrics.cache_hit = True
                logger.info(
                    "נמצאה תשובה במטמון (Cache Hit)",
                    extra={
                        "conversation_id": conversation_id,
                        "response_length": len(cached_response),
                        "cache_lookup_time": metrics.cache_lookup_time
                    }
                )
                metrics.response_length = len(cached_response)
                metrics.total_time = time.time() - start_time
                self.performance_metrics.append(metrics)
                return cached_response

            # חיפוש בשאלות נפוצות
            faq_matches = self.embeddings_manager.find_similar_questions(message)
            if faq_matches:
                best_match = faq_matches[0]  # קבלת ההתאמה הטובה ביותר
                logger.info(
                    "נמצאה תשובה ב-FAQ",
                    extra={
                        "conversation_id": conversation_id,
                        "message": message,
                        "question": best_match[0],
                        "similarity_score": best_match[2]
                    }
                )
                # שמירה במטמון
                self.cache.set(message, best_match[1], conversation_id)
                return best_match[1]

            # זיהוי סוג המשימה
            task_type = self._identify_task_type(message)
            metrics.task_type = task_type
            
            # הוספת ההודעה להיסטוריה
            self.conversation_history.append({"role": "user", "content": message})
            
            # לוג מפורט על הפרומפט
            logger.debug(
                "פרטים על הפרומפט",
                extra={
                    "conversation_id": conversation_id,
                    "system_prompt_length": len(self.base_system_prompt),
                    "user_message_length": len(message),
                    "history_count": len(self.conversation_history),
                    "task_type": task_type
                }
            )

            logger.info(
                "לא נמצאה תשובה במטמון (Cache Miss)",
                extra={
                    "conversation_id": conversation_id,
                    "task_type": task_type,
                    "cache_lookup_time": metrics.cache_lookup_time
                }
            )

            # קבלת הפרמטרים לפי סוג המשימה
            task_params = TaskType.get_prompt_params(task_type)
            
            # יצירת הפרומפט המלא
            messages = self._create_messages(message)
            
            # שליחת הבקשה ל-API
            api_start = time.time()
            assistant_message = await self._make_api_request(
                messages, 
                task_params,
                metrics
            )
            metrics.api_call_time = time.time() - api_start
            metrics.response_length = len(assistant_message)

            # שמירה במטמון
            self.cache.set(message, assistant_message, conversation_id)
            
            metrics.total_time = time.time() - start_time
            self.performance_metrics.append(metrics)
            
            return assistant_message
            
        except Exception as e:
            logger.error(
                "שגיאה בטיפול בהודעה",
                extra={
                    "conversation_id": conversation_id,
                    "error": str(e),
                    "message": message,
                    "duration": time.time() - start_time
                }
            )
            metrics.total_time = time.time() - start_time
            self.performance_metrics.append(metrics)
            return "מצטער, נתקלתי בבעיה. אנא נסה שוב או נסח את השאלה אחרת."

    async def _make_api_request(self, messages: list, task_params: dict, metrics: PerformanceMetrics) -> str:
        """שליחת בקשה ל-API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": messages,
            **task_params
        }
        
        for attempt in range(self.max_retries):
            try:
                metrics.attempt_count += 1
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json=data,
                        timeout=self.timeout
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result["choices"][0]["message"]["content"]
                        else:
                            error_text = await response.text()
                            logger.error(
                                "שגיאה בקריאה ל-API",
                                extra={
                                    "status_code": response.status,
                                    "error": error_text,
                                    "attempt": attempt + 1
                                }
                            )
                            if attempt == self.max_retries - 1:
                                raise Exception(f"API error: {error_text}")
                            await asyncio.sleep(2 ** attempt)  # exponential backoff
                            
            except asyncio.TimeoutError:
                logger.error(
                    "timeout בקריאה ל-API",
                    extra={"attempt": attempt + 1}
                )
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                logger.error(
                    "שגיאה בקריאה ל-API",
                    extra={
                        "error_type": type(e).__name__,
                        "error": str(e),
                        "attempt": attempt + 1
                    }
                )
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

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