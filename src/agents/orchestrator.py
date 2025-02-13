"""
Orchestrator agent that coordinates between user requests and various specialized agents.
"""

import json
import time
import logging
import aiohttp
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from utils import get_logger
from utils.cache_manager import SimpleCache
from utils.embeddings_manager import EmbeddingsManager
from utils.cache import ResponseCache
from utils.metrics import PerformanceMetrics

# יצירת לוגר
logger = get_logger(__name__)

class OrchestratorAgent:
    def __init__(self, deepseek_api_key: str):
        """אתחול הסוכן"""
        self.api_key = deepseek_api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.embeddings_manager = EmbeddingsManager()
        self.cache = SimpleCache(ttl=3600, maxsize=1000)
        self.performance_metrics = []
        self.conversation_history = {}  # מזהה שיחה -> רשימת הודעות
        self.max_retries = 3
        self.timeout = 30
        
        logger.info(
            "סוכן אורקסטרטור אותחל",
            extra={"api_key_length": len(deepseek_api_key) if deepseek_api_key else 0}
        )

    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        קריאה ל-DeepSeek API
        
        Args:
            messages: רשימת הודעות בפורמט של DeepSeek
            
        Returns:
            התשובה מהמודל
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        for attempt in range(self.max_retries):
            try:
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

    def _get_conversation_context(self, conversation_id: str, limit: int = 5) -> str:
        """
        קבלת הקונטקסט של השיחה
        
        Args:
            conversation_id: מזהה השיחה
            limit: כמה הודעות אחרונות לכלול
            
        Returns:
            מחרוזת המתארת את הקונטקסט
        """
        if conversation_id not in self.conversation_history:
            return ""
            
        history = self.conversation_history[conversation_id][-limit:]
        context = "\nהיסטוריית השיחה האחרונה:\n\n"
        
        # מעקב אחר נושאים
        topics = []
        current_topic = None
        last_user_question = None
        
        for i, (role, content) in enumerate(history, 1):
            # זיהוי נושא השיחה
            if role == "משתמש":
                last_user_question = content
                # בדיקה אם ההודעה מתייחסת להודעה קודמת
                if len(content.split()) <= 5 and not any(kw in content.lower() for category, keywords in CATEGORY_KEYWORDS.items() for kw in keywords):
                    # זו כנראה תגובה קצרה להודעה קודמת
                    if current_topic:
                        topics.append(current_topic)
                else:
                    # חיפוש נושא חדש
                    for category, keywords in CATEGORY_KEYWORDS.items():
                        if any(kw in content.lower() for kw in keywords):
                            current_topic = category
                            topics.append(category)
                            break
            
            # הוספת ההודעה עם תיאור ההקשר
            context += f"{role}: {content}\n"
            if current_topic:
                context += f"(נושא: {current_topic})\n"
            context += "\n"
        
        # הוספת סיכום הקשר
        if topics:
            main_topic = max(set(topics), key=topics.count)
            context += f"\nנושא עיקרי בשיחה: {main_topic}\n"
            if last_user_question:
                context += f"שאלה אחרונה: {last_user_question}\n"
            
        return context

    def _create_messages(self, user_message: str, conversation_id: Optional[str] = None) -> List[Dict[str, str]]:
        """יצירת רשימת ההודעות לשליחה ל-API"""
        
        # קבלת הקונטקסט של השיחה
        context = self._get_conversation_context(conversation_id) if conversation_id else ""
        
        # הגדרת הודעת המערכת עם דגש על הקשר השיחה
        system_message = {
            "role": "system",
            "content": f"""אתה עוזר מקצועי לניהול חנות אי-קומרס המתמחה ב-WooCommerce.
תפקידך לסייע למנהלי חנויות בכל הקשור לניהול החנות שלהם.

כללי מענה חשובים:
1. תמיד תן תשובות מעשיות וברורות
2. אם השאלה לא ברורה, שאל שאלת הבהרה ספציפית
3. אם השאלה קצרה, הבן אותה מתוך ההקשר של השיחה
4. תמיד התייחס לנושא האחרון שדובר עליו אם אין נושא חדש
5. הצע דוגמאות מעשיות ומספרים

תחומי המומחיות שלך:
🛍️ ניהול מוצרים והמלאי
💰 מחירים וקופונים
📊 ניתוח נתונים ודוחות
🚚 משלוחים והזמנות
👥 שירות לקוחות
📱 שיווק ופרסום

היסטוריית השיחה:
{context}

זכור: 
- אתה מומחה לניהול חנות, עליך לתת תשובות מקצועיות ומעשיות
- אם המשתמש מבקש מידע נוסף או הרחבה, התייחס לנושא האחרון שדובר עליו
- תמיד הצע דרכים יצירתיות ומעשיות ליישום
- אם אתה לא בטוח במשהו, שאל שאלת הבהרה"""
        }
        
        # הוספת הודעת המשתמש
        user_message = {
            "role": "user",
            "content": user_message
        }
        
        return [system_message, user_message]

    async def handle_message(self, message: str, conversation_id: Optional[str] = None) -> str:
        """טיפול בהודעת משתמש"""
        start_time = time.time()
        metrics = PerformanceMetrics()
        
        try:
            # בדיקה האם צריך הבהרה
            needs_clarification, clarification_question = await self._needs_clarification(message)
            if needs_clarification and clarification_question:
                logger.info(
                    "נדרשת הבהרה לשאלה",
                    extra={
                        "original_message": message,
                        "clarification_question": clarification_question
                    }
                )
                if conversation_id:
                    self._update_conversation_history(conversation_id, message, clarification_question)
                return clarification_question

            if not conversation_id:
                logger.warning("לא התקבל מזהה שיחה, משתמש במזהה ברירת מחדל")
                conversation_id = "default"
            
            # בדיקה במטמון
            cache_start = time.time()
            cached_response = self.cache.get(message, conversation_id)
            metrics.cache_lookup_time = time.time() - cache_start
            
            if cached_response[0]:
                metrics.cache_hit = True
                logger.info(
                    "נמצאה תשובה במטמון (Cache Hit)",
                    extra={
                        "conversation_id": conversation_id,
                        "response_length": len(cached_response[0]),
                        "cache_lookup_time": metrics.cache_lookup_time
                    }
                )
                metrics.response_length = len(cached_response[0])
                metrics.total_time = time.time() - start_time
                self._update_conversation_history(conversation_id, message, cached_response[0])
                self.performance_metrics.append(metrics)
                return cached_response[0]

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

                # יצירת פרומפט למודל השפה
                context = self._get_conversation_context(conversation_id)
                prompt = f"""אתה מומחה מקצועי לניהול חנויות אונליין, עם התמחות ספציפית ב-WooCommerce.
תפקידך לספק מידע מדויק ופרקטי בנושאי ניהול חנות.

להלן מידע רלוונטי מה-FAQ שלנו בנושא השאלה:
{best_match[1]}

הקשר השיחה:
{context}

בהתבסס על המידע הזה, אנא:
1. התאם את התשובה להקשר הספציפי של השאלה
2. הוסף דוגמאות קונקרטיות ומספרים במידת האפשר
3. הצע צעדים מעשיים ליישום
4. שלב טיפים מקצועיים רלוונטיים
5. הצע שאלות המשך אם יש צורך בהבהרות

חשוב:
- התמקד אך ורק בניהול החנות
- תן תשובות מעשיות שאפשר ליישם מיד
- השתמש במונחים מקצועיים אך הסבר אותם
- הצע תמיד את העזרה שלך להמשך

שאלת המשתמש: {message}"""

                # קריאה ל-LLM
                try:
                    messages = [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": message}
                    ]
                    llm_response = await self._call_llm(messages)
                    # שמירה במטמון
                    self.cache.set(message, llm_response, conversation_id)
                    self._update_conversation_history(conversation_id, message, llm_response)
                    return llm_response
                except Exception as e:
                    logger.error(
                        "שגיאה בקריאה ל-LLM",
                        extra={
                            "error": str(e),
                            "conversation_id": conversation_id
                        }
                    )
                    # במקרה של שגיאה, נחזיר את התשובה המקורית מה-FAQ
                    self.cache.set(message, best_match[1], conversation_id)
                    self._update_conversation_history(conversation_id, message, best_match[1])
                    return best_match[1]

            # יצירת הודעות למודל
            messages = self._create_messages(message, conversation_id)
            
            # שליחת בקשה ל-API
            try:
                answer = await self._call_llm(messages)
                
                # שמירה במטמון
                self.cache.set(message, answer, conversation_id)
                
                # עדכון מטריקות
                metrics.response_length = len(answer)
                metrics.total_time = time.time() - start_time
                self.performance_metrics.append(metrics)
                
                # עדכון היסטוריית שיחה
                self._update_conversation_history(conversation_id, message, answer)
                
                return answer
                
            except Exception as e:
                logger.error(
                    "שגיאה בשליחת בקשה ל-API",
                    extra={
                        "error": str(e),
                        "conversation_id": conversation_id
                    }
                )
                raise
                
        except Exception as e:
            logger.error(
                "שגיאה בטיפול בהודעה",
                extra={
                    "error": str(e),
                    "message": message,
                    "conversation_id": conversation_id
                }
            )
            raise

    async def _needs_clarification(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        בדיקה האם השאלה דורשת הבהרה
        
        Args:
            message: הודעת המשתמש
            
        Returns:
            טאפל של (האם צריך הבהרה, שאלת ההבהרה)
        """
        try:
            # יצירת פרומפט לבדיקת הבהרה
            messages = [
                {
                    "role": "system",
                    "content": """בדוק האם השאלה דורשת הבהרה נוספת כדי לתת תשובה מדויקת ומועילה.
אם כן, החזר שאלת הבהרה.
אם לא, החזר "לא".

דוגמאות:
1. שאלה: "איך ליצור קופון?"
   תשובה: "האם הקופון מיועד למוצר ספציפי או לכל החנות?"

2. שאלה: "מה המכירות שלי?"
   תשובה: "לאיזו תקופה תרצה לראות את נתוני המכירות?"

3. שאלה: "איך להוסיף מוצר חדש?"
   תשובה: "לא"
"""
                },
                {
                    "role": "user",
                    "content": f"שאלת המשתמש: {message}"
                }
            ]
            
            # קריאה ל-LLM
            response = await self._call_llm(messages)
            
            # אם התשובה היא "לא", אין צורך בהבהרה
            if response.strip().lower() == "לא":
                return False, None
                
            return True, response.strip()
            
        except Exception as e:
            logger.error(
                "שגיאה בבדיקת הצורך בהבהרה",
                extra={"error": str(e)}
            )
            return False, None

    def _update_conversation_history(self, conversation_id: str, message: str, response: str) -> None:
        """
        עדכון היסטוריית השיחה
        
        Args:
            conversation_id: מזהה השיחה
            message: הודעת המשתמש
            response: תשובת המערכת
        """
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
            
        self.conversation_history[conversation_id].append(("משתמש", message))
        self.conversation_history[conversation_id].append(("מערכת", response))

    def get_performance_stats(self) -> Dict[str, Any]:
        """מחזיר סטטיסטיקות ביצועים"""
        if not self.performance_metrics:
            return {"error": "אין נתוני ביצועים"}
            
        total_requests = len(self.performance_metrics)
        cache_hits = sum(1 for m in self.performance_metrics if m.cache_hit)
        avg_total_time = sum(m.total_time for m in self.performance_metrics) / total_requests
        avg_api_time = sum(m.api_call_time for m in self.performance_metrics if not m.cache_hit) / (total_requests - cache_hits) if total_requests > cache_hits else 0
        
        return {
            "total_requests": total_requests,
            "cache_hits": cache_hits,
            "cache_hit_rate": cache_hits / total_requests,
            "avg_total_time": avg_total_time,
            "avg_api_time": avg_api_time,
            "avg_response_length": sum(m.response_length for m in self.performance_metrics) / total_requests,
            "cache_stats": self.cache.get_stats()
        } 