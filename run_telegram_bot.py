import time
import requests
import logging
from app.core import database
from app.core.config import settings
from app.api.telegram_routes import handle_telegram_incoming_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("telegram_bot")


def main():
    bot_token = settings.telegram_bot_token
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured in settings or .env!")
        return

    logger.info(f"Starting NECO MCS Telegram Bot Runner (@{settings.telegram_bot_username})...")

    # Clear any webhook so long polling receives updates
    try:
        requests.get(f"https://api.telegram.org/bot{bot_token}/deleteWebhook?drop_pending_updates=False", timeout=10)
        logger.info("Webhook cleared successfully. Ready for incoming updates.")
    except Exception as e:
        logger.warning(f"Error clearing webhook: {e}")

    offset = None
    logger.info("Listening for Telegram messages... Press Ctrl+C to stop.")

    while True:
        try:
            params = {"timeout": 25}
            if offset is not None:
                params["offset"] = offset

            resp = requests.get(
                f"https://api.telegram.org/bot{bot_token}/getUpdates",
                params=params,
                timeout=35,
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        msg = update.get("message") or update.get("edited_message")
                        if msg:
                            from_user = msg.get("from", {})
                            logger.info(
                                f"Message from {from_user.get('first_name')} (@{from_user.get('username')}, id={from_user.get('id')}): "
                                f"text='{msg.get('text')}' contact={msg.get('contact')}"
                            )
                            db = database.SessionLocal()
                            try:
                                handle_telegram_incoming_message(msg, db)
                            except Exception as ex:
                                logger.error(f"Error processing message: {ex}", exc_info=True)
                            finally:
                                db.close()
            elif resp.status_code == 409:
                logger.warning("409 Conflict: clearing webhook...")
                requests.get(f"https://api.telegram.org/bot{bot_token}/deleteWebhook", timeout=10)
                time.sleep(2)
            else:
                logger.warning(f"getUpdates returned HTTP {resp.status_code}: {resp.text}")
                time.sleep(3)
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            logger.error(f"Polling loop error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
