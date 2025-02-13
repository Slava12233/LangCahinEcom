"""
מנהל מטמון פשוט המשתמש ב-cachetools
"""

import json
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from cachetools import TTLCache
from utils import get_logger

logger = get_logger(__name__)

class SimpleCache:
    def __init__(self, ttl: int = 3600, maxsize: int = 100):
        """
        אתחול מנהל המטמון
        
        Args:
            ttl: זמן תפוגה בשניות (ברירת מחדל: שעה)
            maxsize: כמות מקסימלית של פריטים במטמון לכל שיחה
        """
        self.ttl = ttl
        self.maxsize = maxsize
        # מילון של מטמונים לפי מזהה שיחה
        self.conversation_caches: Dict[str, TTLCache] = {}
        
        logger.info(
            "מאתחל מערכת מטמון",
            extra={
                "maxsize_per_conversation": maxsize,
                "ttl": ttl
            }
        )

    def _get_or_create_cache(self, conversation_id: str) -> TTLCache:
        """
        מקבל או יוצר מטמון חדש לשיחה ספציפית
        """
        if conversation_id not in self.conversation_caches:
            self.conversation_caches[conversation_id] = TTLCache(
                maxsize=self.maxsize,
                ttl=self.ttl
            )
            logger.info(
                "נוצר מטמון חדש לשיחה",
                extra={"conversation_id": conversation_id}
            )
        return self.conversation_caches[conversation_id]

    def set(self, key: str, value: str, conversation_id: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        שמירת ערך במטמון
        
        Args:
            key: מפתח (שאלת המשתמש)
            value: ערך (תשובת המערכת)
            conversation_id: מזהה השיחה
            context: הקשר השיחה (אופציונלי)
        """
        try:
            cache = self._get_or_create_cache(conversation_id)
            
            cache_data = {
                "value": value,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
            cache[key] = cache_data
            
            logger.debug(
                "נשמר ערך חדש במטמון",
                extra={
                    "conversation_id": conversation_id,
                    "key": key,
                    "value_length": len(value),
                    "has_context": context is not None
                }
            )
            
        except Exception as e:
            logger.error(
                "שגיאה בשמירה במטמון",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "conversation_id": conversation_id
                }
            )

    def get(self, key: str, conversation_id: str, context: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], bool]:
        """
        קבלת ערך מהמטמון
        
        Args:
            key: מפתח (שאלת המשתמש)
            conversation_id: מזהה השיחה
            context: הקשר השיחה (אופציונלי)
            
        Returns:
            tuple: (ערך, האם נמצא) או (None, False) אם לא נמצא
        """
        try:
            if conversation_id not in self.conversation_caches:
                return None, False
                
            cache = self.conversation_caches[conversation_id]
            cached = cache.get(key)
            
            if cached:
                logger.info(
                    "נמצא ערך במטמון",
                    extra={
                        "conversation_id": conversation_id,
                        "key": key,
                        "value_length": len(cached["value"]),
                        "age": (datetime.now() - datetime.fromisoformat(cached["timestamp"])).total_seconds()
                    }
                )
                return cached["value"], True
                
            return None, False
            
        except Exception as e:
            logger.error(
                "שגיאה בחיפוש במטמון",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "conversation_id": conversation_id,
                    "key": key
                }
            )
            return None, False

    def clear_conversation(self, conversation_id: str) -> None:
        """ניקוי המטמון של שיחה ספציפית"""
        try:
            if conversation_id in self.conversation_caches:
                del self.conversation_caches[conversation_id]
                logger.info(
                    "המטמון של השיחה נוקה",
                    extra={"conversation_id": conversation_id}
                )
        except Exception as e:
            logger.error(
                "שגיאה בניקוי מטמון השיחה",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "conversation_id": conversation_id
                }
            )

    def clear_all(self) -> None:
        """ניקוי כל המטמונים"""
        try:
            self.conversation_caches.clear()
            logger.info("כל המטמונים נוקו")
        except Exception as e:
            logger.error(
                "שגיאה בניקוי כל המטמונים",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )

    def get_stats(self) -> Dict[str, Any]:
        """קבלת סטטיסטיקות על המטמון"""
        try:
            stats = {
                "total_conversations": len(self.conversation_caches),
                "conversations": {
                    conv_id: {
                        "entries": len(cache),
                        "maxsize": cache.maxsize,
                        "ttl": self.ttl
                    }
                    for conv_id, cache in self.conversation_caches.items()
                }
            }
            
            logger.info(
                "סטטיסטיקות מטמון",
                extra=stats
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                "שגיאה בקבלת סטטיסטיקות",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            return {
                "error": str(e)
            }

    def clear(self) -> None:
        """ניקוי כל המטמונים"""
        self.conversation_caches.clear()
        logger.info("כל המטמונים נוקו") 