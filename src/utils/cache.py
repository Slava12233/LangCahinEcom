import time
from typing import Dict, Any, Optional, Tuple
import logging

# יצירת לוגר
logger = logging.getLogger(__name__)

class ResponseCache:
    """מטמון לתשובות"""
    
    def __init__(self, ttl: int = 3600, maxsize: int = 1000):
        """
        אתחול המטמון
        
        Args:
            ttl: זמן תפוגה בשניות
            maxsize: גודל מקסימלי של המטמון
        """
        self.ttl = ttl
        self.maxsize = maxsize
        self.cache = {}  # {(conversation_id, key): (value, timestamp)}
        self.hits = 0
        self.misses = 0
        
        logger.info(
            "מטמון אותחל",
            extra={
                "ttl": ttl,
                "maxsize": maxsize
            }
        )
    
    def get(self, key: str, conversation_id: str = "default") -> Tuple[Optional[str], bool]:
        """
        קבלת ערך מהמטמון
        
        Args:
            key: מפתח
            conversation_id: מזהה שיחה
            
        Returns:
            טאפל של (הערך אם נמצא, האם נמצא במטמון)
        """
        cache_key = (conversation_id, key)
        now = time.time()
        
        if cache_key in self.cache:
            value, timestamp = self.cache[cache_key]
            if now - timestamp <= self.ttl:
                self.hits += 1
                logger.debug(
                    "נמצא במטמון",
                    extra={
                        "key": key,
                        "conversation_id": conversation_id,
                        "age": now - timestamp
                    }
                )
                return value, True
                
            # הערך פג תוקף
            del self.cache[cache_key]
            
        self.misses += 1
        logger.debug(
            "לא נמצא במטמון",
            extra={
                "key": key,
                "conversation_id": conversation_id
            }
        )
        return None, False
    
    def set(self, key: str, value: str, conversation_id: str = "default") -> None:
        """
        הגדרת ערך במטמון
        
        Args:
            key: מפתח
            value: ערך
            conversation_id: מזהה שיחה
        """
        cache_key = (conversation_id, key)
        now = time.time()
        
        # ניקוי ערכים שפג תוקפם
        self._cleanup()
        
        # בדיקת גודל המטמון
        if len(self.cache) >= self.maxsize:
            # מחיקת הערך הישן ביותר
            oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
            del self.cache[oldest_key]
            logger.debug(
                "נמחק ערך ישן מהמטמון",
                extra={
                    "key": oldest_key[1],
                    "conversation_id": oldest_key[0]
                }
            )
        
        self.cache[cache_key] = (value, now)
        logger.debug(
            "נשמר ערך במטמון",
            extra={
                "key": key,
                "conversation_id": conversation_id,
                "value_length": len(value)
            }
        )
    
    def _cleanup(self) -> None:
        """ניקוי ערכים שפג תוקפם"""
        now = time.time()
        expired = [
            k for k, (_, ts) in self.cache.items()
            if now - ts > self.ttl
        ]
        for k in expired:
            del self.cache[k]
            
        if expired:
            logger.debug(
                "נוקו ערכים שפג תוקפם",
                extra={"count": len(expired)}
            )
    
    def clear(self) -> None:
        """ניקוי המטמון"""
        self.cache.clear()
        logger.info("המטמון נוקה")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        קבלת סטטיסטיקות על המטמון
        
        Returns:
            מילון עם סטטיסטיקות
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        stats = {
            "size": len(self.cache),
            "maxsize": self.maxsize,
            "ttl": self.ttl,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "conversations": len(set(k[0] for k in self.cache.keys()))
        }
        
        logger.debug(
            "סטטיסטיקות מטמון",
            extra=stats
        )
        
        return stats 