import logging
import os
import time
import asyncio
from decimal import Decimal

from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import config
import db_service
import storage_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    # Ensure user exists in DB
    await asyncio.to_thread(db_service.create_user_if_not_exists, user.id, user.username)
    await update.message.reply_text(
        "Welcome! Use /balance to check your balance. Send a photo or document to upload a receipt."
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    bal = await asyncio.to_thread(db_service.get_balance, user.id)
    await update.message.reply_text(f"Your balance: {bal}")

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = update.effective_user
    if not message or not user:
        return

    file = None
    filename = None
    # photo
    if message.photo:
        tg_file = await message.photo[-1].get_file()
        filename = f"{user.id}_{int(time.time())}_{tg_file.file_unique_id}.jpg"
        download_path = os.path.join("/tmp", filename)
        await tg_file.download_to_drive(download_path)
        saved_path = await asyncio.to_thread(storage_service.save_local, download_path, filename)
    elif message.document:
        tg_file = await message.document.get_file()
        # preserve ext if possible
        ext = os.path.splitext(message.document.file_name or "")[1] or ""
        filename = f"{user.id}_{int(time.time())}_{tg_file.file_unique_id}{ext}"
        download_path = os.path.join("/tmp", filename)
        await tg_file.download_to_drive(download_path)
        saved_path = await asyncio.to_thread(storage_service.save_local, download_path, filename)
    else:
        await message.reply_text("Please send a photo or document as a receipt.")
        return

    # Create pending receipt in DB
    receipt_id = await asyncio.to_thread(db_service.create_receipt, user.id, saved_path, 'pending')

    await message.reply_text("Receipt uploaded and is pending approval. Thank you!")

    # Notify admins with link to whatsapp contact and the uploaded file
    caption = f"New receipt uploaded by @{user.username or user.first_name} (id: {user.id})\nReceipt ID: {receipt_id}\nStatus: pending"
    wa_num = config.ADMIN_WHATSAPP_NUMBER
    wa_link = f"https://wa.me/{wa_num}" if wa_num else ""
    if wa_link:
        caption += f"\nContact via WhatsApp: {wa_link}"

    for admin_id in config.ADMINS:
        try:
            # send file as document to ensure it can be viewed
            await context.bot.send_document(chat_id=admin_id, document=InputFile(saved_path), caption=caption)
        except Exception as e:
            logger.exception(f"Failed to notify admin {admin_id}: {e}")

async def credit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    if user.id not in config.ADMINS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /credit <telegram_id|@username> <amount>")
        return

    target = args[0]
    amount_raw = args[1]
    try:
        amount = float(amount_raw)
    except ValueError:
        await update.message.reply_text("Invalid amount. Use a number.")
        return

    # Resolve user id
    target_user = None
    target_id = None
    if target.startswith("@"):
        target_user = await asyncio.to_thread(db_service.get_user_by_username, target)
        if not target_user:
            await update.message.reply_text("User not found in DB by that username.")
            return
        target_id = int(target_user['telegram_id'])
    else:
        try:
            target_id = int(target)
        except ValueError:
            await update.message.reply_text("Invalid telegram id or username.")
            return

    # Ensure user exists
    await asyncio.to_thread(db_service.create_user_if_not_exists, target_id, None)
    new_balance = await asyncio.to_thread(db_service.update_balance, target_id, amount)

    # Notify target user
    try:
        await context.bot.send_message(chat_id=target_id, text=f"Your account has been credited with {amount}. New balance: {new_balance}")
    except Exception as e:
        logger.exception(f"Failed to notify credited user {target_id}: {e}")

    await update.message.reply_text(f"Credited {amount} to {target}. New balance: {new_balance}")

    # Notify other admins about the credit action and include WhatsApp contact if configured
    wa_num = config.ADMIN_WHATSAPP_NUMBER
    wa_link = f"https://wa.me/{wa_num}" if wa_num else ""
    admin_msg = f"Admin @{user.username or user.first_name} credited {amount} to {target} (id: {target_id}). New balance: {new_balance}"
    if wa_link:
        admin_msg += f"\nContact via WhatsApp: {wa_link}"
    for admin_id in config.ADMINS:
        try:
            if admin_id == user.id:
                continue
            await context.bot.send_message(chat_id=admin_id, text=admin_msg)
        except Exception:
            logger.exception(f"Failed to notify admin {admin_id} about credit")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sorry, I didn't understand that command.")

def main():
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set in environment variables.")
        return

    # Ensure DB initialized
    try:
        db_service.init_db()
    except Exception as e:
        logger.exception("Failed to initialize DB: %s", e)

    application = ApplicationBuilder().token(config.BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("credit", credit_command))

    # receipt handler (photos and documents)
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt))

    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info("Bot started")
    application.run_polling()

if __name__ == '__main__':
    main()
