"""
מודול לוגים מרכזי לכל המערכת.
מספק פונקציונליות לוגים אחידה עם:
- רמות לוג שונות
- פורמט אחיד
- שמירה לקבצים לפי תאריך
- רוטציה של קבצי לוג
"""

import os
import logging
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any

# קונפיגורציה בסיסית
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEBUG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# הגדרת נתיבים
ROOT_DIR = Path(__file__).parent.parent.parent
LOGS_DIR = ROOT_DIR / 'logs'

class CustomLogger:
    """
    מחלקה מרכזית לניהול לוגים במערכת.
    מאפשרת:
    - כתיבת לוגים לקובץ ולמסוף
    - פורמט אחיד
    - רוטציה של קבצים
    - תמיכה במידע מובנה (JSON)
    """
    
    def __init__(self, name: str, level: str = 'INFO'):
        """
        אתחול הלוגר.
        
        Args:
            name: שם הלוגר (בד"כ שם המודול)
            level: רמת הלוג ההתחלתית
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        
        # מניעת כפילות לוגים
        self.logger.propagate = False
        
        # יצירת תיקיית הלוגים אם לא קיימת
        if not LOGS_DIR.exists():
            LOGS_DIR.mkdir(parents=True)
        
        # הגדרת הפורמט
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        debug_formatter = logging.Formatter(DEBUG_FORMAT, DATE_FORMAT)
        
        # הגדרת handler לקובץ היומי
        daily_handler = TimedRotatingFileHandler(
            filename=LOGS_DIR / 'app.log',
            when='midnight',
            interval=1,
            backupCount=30,  # שמירת 30 ימים אחורה
            encoding='utf-8'
        )
        daily_handler.setFormatter(formatter)
        self.logger.addHandler(daily_handler)
        
        # הגדרת handler לקובץ שגיאות
        error_handler = RotatingFileHandler(
            filename=LOGS_DIR / 'error.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(debug_formatter)
        self.logger.addHandler(error_handler)
        
        # הגדרת handler למסוף
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # מידע על השיחה הנוכחית
        self.conversation_id: Optional[str] = None
        self.user_id: Optional[str] = None
    
    def set_conversation_context(self, conversation_id: str, user_id: str) -> None:
        """
        הגדרת הקונטקסט של השיחה הנוכחית.
        
        Args:
            conversation_id: מזהה השיחה
            user_id: מזהה המשתמש
        """
        self.conversation_id = conversation_id
        self.user_id = user_id
    
    def _format_message(self, message: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """
        פורמט ההודעה עם מידע נוסף.
        
        Args:
            message: ההודעה המקורית
            extra: מידע נוסף להוספה
        
        Returns:
            ההודעה המפורמטת
        """
        data = {
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'conversation_id': self.conversation_id,
            'user_id': self.user_id
        }
        
        if extra:
            data.update(extra)
        
        return json.dumps(data, ensure_ascii=False)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """רישום הודעת debug."""
        self.logger.debug(self._format_message(message, extra))
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """רישום הודעת info."""
        self.logger.info(self._format_message(message, extra))
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """רישום הודעת warning."""
        self.logger.warning(self._format_message(message, extra))
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """רישום הודעת error."""
        self.logger.error(self._format_message(message, extra))
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """רישום הודעת critical."""
        self.logger.critical(self._format_message(message, extra))

# יצירת instance יחיד של הלוגר
def get_logger(name: str) -> CustomLogger:
    """
    קבלת instance של הלוגר.
    
    Args:
        name: שם המודול
    
    Returns:
        CustomLogger instance
    """
    return CustomLogger(name) 