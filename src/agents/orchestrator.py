"""
Orchestrator agent that coordinates between user requests and various specialized agents.
"""

import json
from typing import Dict, Any
import requests
import aiohttp
import hashlib
from typing import Optional
import asyncio
from cachetools import TTLCache

from utils import get_logger

# יצירת לוגר ייעודי ל-Orchestrator
logger = get_logger(__name__)

class OrchestratorAgent:
    def __init__(self, deepseek_api_key: str):
        """Initialize the orchestrator with necessary components."""
        self.api_key = deepseek_api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.conversation_history = []
        self.max_retries = 3  # מספר נסיונות מקסימלי
        self.timeout = 30  # timeout של 30 שניות
        
        # יצירת מטמון עם TTL של שעה אחת (3600 שניות) ומקסימום 1000 פריטים
        self.response_cache = TTLCache(maxsize=1000, ttl=3600)
        
        logger.info(
            "מאתחל את ה-Orchestrator",
            extra={
                "api_url": self.api_url,
                "api_key_length": len(self.api_key) if self.api_key else 0,
                "timeout": self.timeout,
                "max_retries": self.max_retries
            }
        )
        
        # הגדרת הפונקציות שהמודל יכול להשתמש בהן
        self.functions = [
            {
                "name": "get_store_info",
                "description": "Get basic information about the store",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "products_count": {"type": "integer"},
                        "orders_today": {"type": "integer"},
                        "status": {"type": "string"}
                    }
                }
            }
        ]
        
        logger.debug(
            "נרשמו הפונקציות הזמינות למודל",
            extra={
                "functions_count": len(self.functions),
                "functions": [f["name"] for f in self.functions]
            }
        )
        
        self.system_prompt = """אתה עוזר חכם לניהול חנות מקוונת. תפקידך לעזור למנהלי החנות בניהול המוצרים, 
        המכירות וההזמנות. אתה צריך להיות:
        1. מקצועי ומדויק במידע שאתה מספק 📊
        2. יעיל בביצוע משימות ⚡
        3. יוזם ומציע רעיונות לשיפור כשרלוונטי 💡
        4. תמיד לשמור על טון ידידותי ומכבד 😊

        חשוב מאוד:
        - תן תשובות קצרות וממוקדות
        - התמקד במידע החשוב ביותר
        - השתמש בנקודות במקום פסקאות ארוכות
        - הימנע מחזרות מיותרות

        חשוב להשתמש באימוג'ים מתאימים בתשובות שלך כדי להפוך אותן ליותר ידידותיות וברורות.
        למשל:
        - כשמדברים על מוצרים: 📦
        - כשמדברים על מכירות: 💰
        - כשמדברים על לקוחות: 👥
        - כשמדברים על הזמנות: 🛒
        - כשמדברים על סטטיסטיקות: 📈
        - כשמדברים על בעיות או שגיאות: ⚠️
        - כשנותנים טיפים או עצות: 💡
        - כשמציינים הצלחה: ✅
        - כשמציינים כישלון או שגיאה: ❌

        כשאתה לא בטוח במשהו, תמיד תבקש הבהרה לפני שתבצע פעולות ❓
        """

    def _generate_cache_key(self, message: str, context: list) -> str:
        """
        יצירת מפתח ייחודי למטמון על בסיס ההודעה וההקשר.
        """
        # יצירת מחרוזת המייצגת את ההודעה וההקשר
        cache_str = f"{message}|{json.dumps([msg for msg in context if msg['role'] != 'system'])}"
        # יצירת hash מהמחרוזת
        return hashlib.sha256(cache_str.encode()).hexdigest()

    async def handle_user_message(self, message: str) -> str:
        """
        Process user message and return appropriate response.
        Now with retry mechanism.
        """
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": message})
            
            logger.info(
                "מתחיל לטפל בהודעת משתמש חדשה",
                extra={
                    "message_length": len(message),
                    "conversation_history_length": len(self.conversation_history),
                    "message_preview": message[:50] if len(message) > 50 else message
                }
            )
            
            # בדיקה אם התשובה קיימת במטמון
            cache_key = self._generate_cache_key(message, self.conversation_history)
            cached_response = self.response_cache.get(cache_key)
            
            if cached_response:
                logger.info(
                    "נמצאה תשובה במטמון",
                    extra={
                        "cache_key": cache_key,
                        "response_length": len(cached_response)
                    }
                )
                return cached_response

            # Prepare the request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history
                ],
                "temperature": 0.3,
                "max_tokens": 300
            }

            # ניסיון עם מספר retries
            for attempt in range(self.max_retries):
                try:
                    logger.debug(
                        f"ניסיון {attempt + 1} מתוך {self.max_retries}",
                        extra={
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "timeout": self.timeout
                        }
                    )
                    
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(self.api_url, headers=headers, json=data) as response:
                            response.raise_for_status()
                            result = await response.json()
                            
                            # Parse response
                            assistant_message = result["choices"][0]["message"]["content"]
                            
                            logger.info(
                                "התקבלה תשובה מ-DeepSeek API",
                                extra={
                                    "response_length": len(assistant_message),
                                    "response_preview": assistant_message[:50] if len(assistant_message) > 50 else assistant_message,
                                    "attempt": attempt + 1
                                }
                            )
                            
                            # בדיקה שהתשובה לא קצרה מדי
                            if len(assistant_message) < 100:  # אם התשובה קצרה מ-100 תווים
                                logger.warning(
                                    "התקבלה תשובה קצרה מדי, מנסה שוב",
                                    extra={
                                        "response_length": len(assistant_message),
                                        "attempt": attempt + 1
                                    }
                                )
                                if attempt < self.max_retries - 1:  # אם זה לא הניסיון האחרון
                                    continue  # נסה שוב
                            
                            # Check if the model wants to call a function
                            if "function_call" in result["choices"][0]["message"]:
                                function_call = result["choices"][0]["message"]["function_call"]
                                logger.debug(
                                    "המודל מבקש להפעיל פונקציה",
                                    extra={
                                        "function_name": function_call["name"],
                                        "function_args": function_call.get("arguments", "")
                                    }
                                )
                                
                                if function_call["name"] == "get_store_info":
                                    store_info = self._get_store_info()
                                    logger.info(
                                        "מחזיר מידע על החנות",
                                        extra={"store_info": store_info}
                                    )
                                    # Add function response to conversation
                                    self.conversation_history.append({
                                        "role": "function",
                                        "name": "get_store_info",
                                        "content": json.dumps(store_info)
                                    })
                                    # Get final response from model
                                    return await self.handle_user_message("תוכל להציג לי את המידע על החנות בצורה ברורה?")
                            
                            # Add assistant's response to conversation history
                            self.conversation_history.append({"role": "assistant", "content": assistant_message})
                            
                            # שמירת התשובה במטמון
                            self.response_cache[cache_key] = assistant_message
                            
                            return assistant_message
                            
                except asyncio.TimeoutError:
                    logger.warning(
                        f"Timeout בניסיון {attempt + 1}",
                        extra={
                            "attempt": attempt + 1,
                            "timeout": self.timeout
                        }
                    )
                    if attempt == self.max_retries - 1:  # אם זה הניסיון האחרון
                        raise
                    await asyncio.sleep(1)  # המתנה של שנייה לפני הניסיון הבא
                    
                except aiohttp.ClientError as e:
                    logger.error(
                        f"שגיאת רשת בניסיון {attempt + 1}",
                        extra={
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "attempt": attempt + 1
                        }
                    )
                    if attempt == self.max_retries - 1:  # אם זה הניסיון האחרון
                        raise
                    await asyncio.sleep(1)  # המתנה של שנייה לפני הניסיון הבא

            # אם הגענו לכאן, כל הניסיונות נכשלו
            raise Exception("כל הניסיונות נכשלו")

        except Exception as e:
            logger.error(
                "שגיאה בטיפול בהודעה",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "message": message
                }
            )
            return "מצטער, נתקלתי בבעיה בעיבוד הבקשה שלך. אנא נסה שוב או נסח את השאלה בצורה אחרת."

    def _get_store_info(self) -> Dict[str, Any]:
        """Temporary mock function for store information."""
        logger.debug("מחזיר מידע מדומה על החנות")
        return {
            "name": "החנות שלי",
            "products_count": 150,
            "orders_today": 5,
            "status": "active"
        } 