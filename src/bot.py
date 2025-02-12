"""
Telegram bot implementation for the Ultimate Store Manager.
This module handles all Telegram-related functionality and message routing.
"""

import os
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from utils import get_logger

# יצירת לוגר ייעודי לבוט
logger = get_logger(__name__)

class StoreManagerBot:
    def __init__(self, token: str, orchestrator=None):
        """Initialize the bot with the given token and optional orchestrator."""
        self.token = token
        self.orchestrator = orchestrator
        self.app = Application.builder().token(self.token).build()
        self.register_handlers()
        logger.info("בוט טלגרם אותחל בהצלחה", extra={"token_prefix": self.token[:10]})

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        user = update.effective_user
        logger.info(
            "התקבלה פקודת start", 
            extra={
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name
            }
        )
        
        welcome_message = (
            f"שלום {user.first_name}! 👋\n\n"
            "אני העוזר החכם שלך לניהול החנות. אשמח לעזור לך ב:\n\n"
            "📚 מידע והדרכה:\n"
            "• טיפים לניהול חנות מוצלחת\n"
            "• המלצות לשיפור המכירות\n"
            "• מענה לשאלות נפוצות\n\n"
            "💡 ייעוץ מקצועי:\n"
            "• אסטרטגיות שיווק\n"
            "• אופטימיזציה של החנות\n"
            "• פתרונות לאתגרים נפוצים\n\n"
            "🔜 בקרוב יתווספו יכולות חדשות כמו:\n"
            "• הצגת נתונים בזמן אמת\n"
            "• ביצוע פעולות ניהול\n"
            "• ניתוח מגמות ותובנות\n\n"
            "איך אוכל לעזור לך היום? 😊"
        )
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        user = update.effective_user
        logger.info(
            "התקבלה פקודת help",
            extra={
                "user_id": user.id,
                "username": user.username
            }
        )
        
        help_message = (
            "הנה מה שאני יכול לעזור לך איתו:\n\n"
            "📦 *ניהול מוצרים*\n"
            "• הצגת מוצרים\n"
            "• עדכון מלאי\n"
            "• שינוי מחירים\n\n"
            "💰 *מכירות והזמנות*\n"
            "• סטטוס הזמנות\n"
            "• דוחות מכירות\n"
            "• ניתוח מגמות\n\n"
            "🔍 *מידע ומחקר*\n"
            "• מחקר שוק\n"
            "• ניתוח מתחרים\n"
            "• המלצות לשיפור\n\n"
            "פשוט שאל אותי בשפה טבעית ואני אשתדל לעזור! 😊"
        )
        await update.message.reply_text(help_message, parse_mode="Markdown")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
        user = update.effective_user
        user_message = update.message.text
        
        # הגדרת קונטקסט השיחה בלוגר
        logger.set_conversation_context(
            conversation_id=str(update.effective_chat.id),
            user_id=str(user.id)
        )
        
        logger.info(
            "התקבלה הודעה חדשה",
            extra={
                "user_id": user.id,
                "username": user.username,
                "message_length": len(user_message),
                "message_preview": user_message[:50] if len(user_message) > 50 else user_message
            }
        )

        if not self.orchestrator:
            logger.warning(
                "הבוט עדיין בתהליך הגדרה",
                extra={"user_id": user.id}
            )
            await update.message.reply_text("מצטער, אני עדיין בתהליך הגדרה. אנא נסה שוב בקרוב.")
            return

        try:
            # שליחת הודעת המתנה
            waiting_message = await update.message.reply_text("🤔 מעבד את הבקשה שלך... אנא המתן")
            
            logger.debug(
                "שולח הודעה לטיפול ה-Orchestrator",
                extra={
                    "user_id": user.id,
                    "message": user_message
                }
            )
            
            response = self.orchestrator.handle_user_message(user_message)
            
            logger.info(
                "התקבלה תשובה מה-Orchestrator",
                extra={
                    "user_id": user.id,
                    "response_length": len(response)
                }
            )
            
            # מחיקת הודעת ההמתנה
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=waiting_message.message_id
            )
            
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(
                "שגיאה בטיפול בהודעה",
                extra={
                    "user_id": user.id,
                    "error": str(e),
                    "message": user_message
                }
            )
            await update.message.reply_text(
                "מצטער, נתקלתי בבעיה בעיבוד הבקשה שלך. אנא נסה שוב מאוחר יותר."
            )

    def register_handlers(self) -> None:
        """Register all message handlers."""
        logger.debug("רושם handlers לבוט")
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.add_error_handler(self.error_handler)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the telegram-python-bot library."""
        logger.error(
            "שגיאה בטיפול בעדכון",
            extra={
                "error": str(context.error),
                "update": str(update) if update else None
            }
        )

    def run(self) -> None:
        """Start the bot."""
        logger.info("מתחיל להריץ את הבוט...")
        self.app.run_polling() 