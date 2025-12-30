import os
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Read bot token from environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.warning("Environment variable BOT_TOKEN not set. The bot will not run without a token.")


def start(update: Update, context: CallbackContext) -> None:
    """
    Interactive /start handler.
    Sends a personalized welcome message with the user's name and id and shows an inline keyboard
    with actions: Request Sick Leave, Balance, Help, Charge via WhatsApp.
    """
    user = update.effective_user
    if not user:
        update.message.reply_text("Hello — I couldn't determine your user info.")
        return

    name = user.first_name or user.full_name or user.username or "there"
    user_id = user.id

    welcome_text = (
        f"Hello, {name}! 👋\n"
        f"Your ID: {user_id}\n\n"
        "Welcome to the Zero bot. Use the buttons below to make a request or check your balance."
    )

    keyboard = [
        [InlineKeyboardButton("Request Sick Leave 📝", callback_data="req_sick")],
        [InlineKeyboardButton("Balance 💳", callback_data="balance")],
        [
            InlineKeyboardButton("Help ❓", callback_data="help"),
            InlineKeyboardButton("Charge via WhatsApp 📲", callback_data="charge_whatsapp"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(welcome_text, reply_markup=reply_markup)


def _get_balance_for_user(user_id: int) -> str:
    """
    Placeholder function to retrieve the user's balance.
    Replace with real logic (DB/API) as needed.
    """
    # For example purposes, return a dummy balance
    # In a real implementation you would query your database or service here
    balance_amount = 42.0
    return f"{balance_amount:.2f} credits"


def balance(update: Update, context: CallbackContext) -> None:
    """
    Command handler for /balance — sends the user's balance.
    """
    user = update.effective_user
    user_id = user.id if user else None
    if user_id is None:
        update.message.reply_text("Could not determine your user ID to fetch the balance.")
        return

    bal = _get_balance_for_user(user_id)
    update.message.reply_text(f"Your current balance is: {bal}")


def handle_receipt(update: Update, context: CallbackContext) -> None:
    """
    Handler for receipts or uploaded payment proofs.
    This is a simple placeholder that acknowledges the receipt.
    """
    # In many bots, receipts may be images or documents — we just acknowledge here
    update.message.reply_text("Thanks — we received your receipt. We'll process it and update your balance shortly.")


def credit_command(update: Update, context: CallbackContext) -> None:
    """
    Handler for /credit command (example).
    """
    # Placeholder: guide user how to credit their account
    update.message.reply_text(
        "To credit your account, please send a receipt via this chat or use the Charge via WhatsApp button from /start."
    )


def unknown(update: Update, context: CallbackContext) -> None:
    """
    Handler for unknown commands.
    """
    update.message.reply_text("Sorry, I didn't understand that command. Use /start to see available options.")


def button_callback(update: Update, context: CallbackContext) -> None:
    """
    CallbackQueryHandler to handle button presses from the inline keyboard.
    Supports: req_sick, balance, help, charge_whatsapp
    """
    query = update.callback_query
    if not query:
        return

    # Acknowledge the callback (this removes the loading state on the client)
    query.answer()

    data = query.data
    user = query.from_user
    user_id = user.id if user else None

    if data == "balance":
        if user_id is None:
            query.edit_message_text("Could not determine your user ID to fetch the balance.")
            return
        bal = _get_balance_for_user(user_id)
        query.edit_message_text(f"Your current balance is: {bal}")

    elif data == "req_sick":
        # Simple instructions to request sick leave
        text = (
            "To request sick leave:\n"
            "1. Send a brief message explaining your situation.\n"
            "2. Attach any medical note or receipt as a photo/document.\n"
            "3. Our HR team will review and reply with confirmation.\n\n"
            "You can attach the medical note now in this chat."
        )
        query.edit_message_text(text)

    elif data == "help":
        text = (
            "Help - available commands:\n"
            "/start - Show welcome and actions\n"
            "/balance - Show your current balance\n"
            "/credit - Get instructions to credit your account\n"
            "Or press the buttons shown in /start for quick actions."
        )
        query.edit_message_text(text)

    elif data == "charge_whatsapp":
        # Provide a WhatsApp link — replace the phone number with the real one if you have it
        whatsapp_number = os.environ.get("WHATSAPP_NUMBER", "1234567890")
        wa_link = f"https://wa.me/{whatsapp_number}"
        text = (
            "To charge your account via WhatsApp, open the link below and follow the instructions:\n"
            f"{wa_link}\n\n"
            "Make sure to include your user ID when you contact support so we can apply the credit quickly."
        )
        query.edit_message_text(text)

    else:
        query.edit_message_text("Unknown action. Please use /start to see available options.")


def main() -> None:
    """
    Entry point for the bot. Registers handlers including the CallbackQueryHandler.
    """
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN provided; exiting.")
        return

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("credit", credit_command))

    # Register callback query handler for inline buttons
    dp.add_handler(CallbackQueryHandler(button_callback))

    # Register a handler for receipts (photos/documents) — simple acknowledgment
    dp.add_handler(MessageHandler(Filters.photo | Filters.document, handle_receipt))

    # Unknown commands
    dp.add_handler(MessageHandler(Filters.command, unknown))

    # Start the Bot
    updater.start_polling()
    logger.info("Bot started. Listening for updates...")
    updater.idle()


if __name__ == "__main__":
    main()
