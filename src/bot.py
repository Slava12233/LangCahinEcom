"""
Telegram bot implementation for the Ultimate Store Manager.
This module handles all Telegram-related functionality and message routing.
"""

import logging
import asyncio
from typing import Dict, Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from agents.orchestrator import OrchestratorAgent
from utils import get_logger
from utils.constants import QuestionCategory, QuestionIntent

# Configure logging
logger = get_logger(__name__)

class StoreManagerBot:
    def __init__(self, token: str, orchestrator: OrchestratorAgent):
        """Initialize the bot with the given token and orchestrator."""
        self.token = token
        self.orchestrator = orchestrator
        self.application = Application.builder().token(token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
        
        logger.info("בוט אותחל בהצלחה")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a welcome message when the command /start is issued."""
        user = update.effective_user
        welcome_message = f"""שלום {user.first_name}! 👋

אני העוזר החכם שלך לניהול החנות. אני יכול לעזור לך עם:
🛍️ ניהול מוצרים והזמנות
📊 דוחות מכירות וביצועים
🎯 שיווק וקידום מכירות
👥 שירות לקוחות
🔧 תמיכה טכנית

פשוט שאל אותי כל שאלה בנושאים אלו ואשמח לעזור!

לרשימת הפקודות הזמינות, הקלד /help"""

        await update.message.reply_text(welcome_message)
        logger.info(
            "נשלחה הודעת פתיחה",
            extra={
                "user_id": user.id,
                "username": user.username
            }
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a help message when the command /help is issued."""
        help_message = """הנה מה שאני יכול לעזור לך איתו:

📦 *ניהול מוצרים*
- מידע על מוצרים
- הוספת/עריכת מוצרים
- ניהול מלאי

🛒 *הזמנות*
- סטטוס הזמנות
- עדכון הזמנות
- מעקב משלוחים

📊 *דוחות וניתוח*
- דוחות מכירות
- ניתוח ביצועים
- מגמות ותובנות

🎯 *שיווק וקידום*
- יצירת מבצעים
- ניהול קופונים
- אסטרטגיות קידום

👥 *שירות לקוחות*
- טיפול בפניות
- החזרות וזיכויים
- שאלות נפוצות

פשוט שאל אותי כל שאלה בנושאים אלו ואשמח לעזור!"""

        await update.message.reply_text(help_message, parse_mode='Markdown')
        logger.info(
            "נשלחה הודעת עזרה",
            extra={
                "user_id": update.effective_user.id,
                "username": update.effective_user.username
            }
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
        user = update.effective_user
        message = update.message.text
        chat_id = update.effective_chat.id
        
        logger.info(
            "התקבלה הודעה חדשה",
            extra={
                "user_id": user.id,
                "username": user.username,
                "chat_id": chat_id,
                "message": message
            }
        )

        try:
            # שליחת הודעת המתנה
            waiting_message = await update.message.reply_text("🤔 מעבד את הבקשה שלך... אנא המתן")
            logger.debug("נשלחה הודעת המתנה")
            
            # קבלת תשובה מהאורקסטרטור
            response = await self.orchestrator.handle_message(
                message=message,
                conversation_id=str(chat_id)
            )
            
            # מחיקת הודעת ההמתנה
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=waiting_message.message_id
                )
                logger.debug("הודעת ההמתנה נמחקה")
            except Exception as e:
                logger.warning(
                    "לא הצלחתי למחוק את הודעת ההמתנה",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
            
            # שליחת התשובה למשתמש
            await update.message.reply_text(response)
            
            logger.info(
                "נשלחה תשובה בהצלחה",
                extra={
                    "user_id": user.id,
                    "chat_id": chat_id,
                    "response_length": len(response)
                }
            )
            
        except Exception as e:
            error_message = """מצטער, נתקלתי בבעיה בעיבוד הבקשה שלך.
אנא נסה שוב או צור קשר עם התמיכה אם הבעיה נמשכת."""
            
            await update.message.reply_text(error_message)
            
            logger.error(
                "שגיאה בטיפול בהודעה",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": user.id,
                    "chat_id": chat_id,
                    "message": message
                },
                exc_info=True
            )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the bot."""
        logger.error(
            "שגיאה בבוט",
            extra={
                "error": str(context.error),
                "error_type": type(context.error).__name__,
                "update": update
            },
            exc_info=context.error
        )
        
        # שליחת הודעת שגיאה למשתמש אם אפשר
        if isinstance(update, Update) and update.effective_message:
            error_message = """מצטער, נתקלתי בבעיה בלתי צפויה.
אנא נסה שוב מאוחר יותר או צור קשר עם התמיכה."""
            
            await update.effective_message.reply_text(error_message)

    def run(self) -> None:
        """Start the bot."""
        logger.info("מתחיל להריץ את הבוט...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES) 