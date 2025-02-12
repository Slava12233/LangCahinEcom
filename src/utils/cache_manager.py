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
            maxsize: כמות מקסימלית של פריטים במטמון
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.ttl = ttl
        
        logger.info(
            "מאתחל מטמון",
            extra={
                "maxsize": maxsize,
                "ttl": ttl
            }
        )

    def set(self, key: str, value: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        שמירת ערך במטמון
        
        Args:
            key: מפתח (שאלת המשתמש)
            value: ערך (תשובת המערכת)
            context: הקשר השיחה (אופציונלי)
        """
        try:
            cache_data = {
                "value": value,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
            self.cache[key] = cache_data
            
            logger.debug(
                "נשמר ערך חדש במטמון",
                extra={
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
                    "error_message": str(e)
                }
            )

    def get(self, key: str, context: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], bool]:
        """
        קבלת ערך מהמטמון
        
        Args:
            key: מפתח (שאלת המשתמש)
            context: הקשר השיחה (אופציונלי)
            
        Returns:
            tuple: (ערך, האם נמצא) או (None, False) אם לא נמצא
        """
        try:
            cached = self.cache.get(key)
            if cached:
                logger.info(
                    "נמצא ערך במטמון",
                    extra={
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
                    "key": key
                }
            )
            return None, False

    def clear(self) -> None:
        """ניקוי המטמון"""
        try:
            self.cache.clear()
            logger.info("המטמון נוקה בהצלחה")
        except Exception as e:
            logger.error(
                "שגיאה בניקוי המטמון",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )

    def get_stats(self) -> Dict[str, Any]:
        """קבלת סטטיסטיקות על המטמון"""
        try:
            stats = {
                "total_entries": len(self.cache),
                "maxsize": self.cache.maxsize,
                "ttl": self.ttl
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