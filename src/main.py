"""
Main entry point for the Ultimate Store Manager bot.
"""

import os
import logging
from dotenv import load_dotenv
from pathlib import Path

from bot import StoreManagerBot
from agents.orchestrator import OrchestratorAgent
from agents.woocommerce_agent import WooCommerceAgent

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger = logging.getLogger(__name__)

def main():
    """Initialize and start the bot."""
    # Load environment variables from root directory
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        logger.error(f"Environment file not found at {env_path}")
        return
    
    # Load environment variables with override=True to ensure values are updated
    load_dotenv(dotenv_path=env_path, override=True)

    # Debug: Print environment variables
    logger.info(f"Environment file path: {env_path}")
    logger.info(f"Environment file exists: {env_path.exists()}")
    logger.info(f"TELEGRAM_BOT_TOKEN: {os.getenv('TELEGRAM_BOT_TOKEN')}")
    logger.info(f"DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY')}")
    logger.info(f"WC_STORE_URL: {os.getenv('WC_STORE_URL')}")

    # Validate required environment variables
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "DEEPSEEK_API_KEY",
        "WC_STORE_URL",
        "WC_CONSUMER_KEY",
        "WC_CONSUMER_SECRET"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return

    try:
        # Initialize WooCommerce agent
        wc_agent = WooCommerceAgent(
            url=os.getenv("WC_STORE_URL"),
            consumer_key=os.getenv("WC_CONSUMER_KEY"),
            consumer_secret=os.getenv("WC_CONSUMER_SECRET")
        )

        # Initialize Orchestrator agent
        orchestrator = OrchestratorAgent(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY")
        )

        # Initialize and start the bot
        bot = StoreManagerBot(
            token=os.getenv("TELEGRAM_BOT_TOKEN"),
            orchestrator=orchestrator
        )

        logger.info("Starting the Ultimate Store Manager bot...")
        bot.run()

    except Exception as e:
        logger.error(f"Failed to start the bot: {e}")
        raise

if __name__ == "__main__":
    main() 