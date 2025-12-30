"""
import logging
import uuid
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters, CallbackQueryHandler
)
from config import BOT_TOKEN, SAR_TO_YER_RATE, REQUIRED_YER_AMOUNT
from db_service import DBService
from payment_service import verify_kuraimi_payment
from pdf_generator import generate_sick_leave_pdf

logging.basicConfig(level=logging.INFO)

# States
NAME, DURATION, AWAIT_RECEIPT = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton('طلب إجازة مرضية', callback_data='request')]]
    await update.message.reply_text('مرحبًا! اختر ما تود فعله:', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'request':
        await query.message.reply_text('الرجاء إرسال اسم المريض بالكامل:')
        return NAME
    return ConversationHandler.END

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['patient_name'] = update.message.text
    await update.message.reply_text('كم مدة الإجازة؟ (مثال: يوم، يومين)')
    return DURATION

async def duration_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['duration'] = update.message.text

    # show summary and payment instructions
    amount = REQUIRED_YER_AMOUNT
    summary = f"ملخص الطلب:\nالاسم: {context.user_data['patient_name']}\nمدة الإجازة: {context.user_data['duration']}\nالمبلغ المطلوب: {amount} ر.ي\n\nالرجاء تحويل المبلغ إلى حساب التاجر في الكريمي وإرسال صورة الإيصال هنا."
    await update.message.reply_text(summary)
    return AWAIT_RECEIPT

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # save receipt locally
    photo = update.message.photo[-1]
    file = await photo.get_file()
    tmp_file = f"/tmp/receipt_{uuid.uuid4().hex}.jpg"
    await file.download_to_drive(tmp_file)

    # verify payment (simulate)
    amount = REQUIRED_YER_AMOUNT
    verified = await verify_kuraimi_payment(amount=amount, receipt_file_path=tmp_file)

    if not verified:
        await update.message.reply_text('لم نتمكن من التحقق من الدفع. الرجاء المحاولة أو الاتصال بالدعم.')
        return ConversationHandler.END

    # generate UUID and save to DB
    leave_uuid = str(uuid.uuid4())
    record = {
        'id': leave_uuid,
        'user_id': update.message.from_user.id,
        'patient_name': context.user_data.get('patient_name'),
        'duration': context.user_data.get('duration'),
        'amount': amount,
        'payment_status': 'paid',
        'receipt_url': None
    }

    db = DBService()
    try:
        db.init_db()
        db.save_sick_leave(record)
    finally:
        db.close()

    # generate pdf
    pdf_path = generate_sick_leave_pdf({
        'patient_name': record['patient_name'],
        'duration': record['duration'],
        'uuid': leave_uuid,
        'amount': amount
    })

    # send pdf to user
    await update.message.reply_document(open(pdf_path, 'rb'))

    # cleanup tmp files
    try:
        os.remove(pdf_path)
        os.remove(tmp_file)
    except Exception:
        pass

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('تم إلغاء العملية.')
    return ConversationHandler.END

def main():
    if not BOT_TOKEN:
        raise RuntimeError('BOT_TOKEN not set in environment')

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^request$')],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, duration_handler)],
            AWAIT_RECEIPT: [MessageHandler(filters.PHOTO, receipt_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv)

    app.run_polling()

if __name__ == '__main__':
    main()
"""
