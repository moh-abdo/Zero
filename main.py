import logging
import uuid
import os
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters, CallbackQueryHandler
)
from config import BOT_TOKEN, SAR_TO_YER_RATE, REQUIRED_YER_AMOUNT, TEMP_PDF_DIR
from db_service import DBService
from payment_service import verify_kuraimi_payment
from pdf_generator import generate_sick_leave_pdf
from storage_service import upload_receipt

logging.basicConfig(level=logging.INFO)

# States
NAME, DURATION, AWAIT_RECEIPT = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton('طلب إجازة مرضية', callback_data='request')]]
    # If update is a callback query, reply accordingly
    if update.message:
        await update.message.reply_text('مرحبًا! اختر ما تود فعله:', reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text('مرحبًا! اختر ما تود فعله:', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'request':
        await query.message.reply_text('الرجاء إرسال اسم المريض بالكامل:')
        return NAME
    return ConversationHandler.END

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['patient_name'] = update.message.text.strip()
    await update.message.reply_text('كم مدة الإجازة؟ (مثال: يوم، يومين)')
    return DURATION

async def duration_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['duration'] = update.message.text.strip()

    # show summary and payment instructions
    amount = REQUIRED_YER_AMOUNT
    summary = (
        f"ملخص الطلب:\n"
        f"الاسم: {context.user_data['patient_name']}\n"
        f"مدة الإجازة: {context.user_data['duration']}\n"
        f"المبلغ المطلوب: {amount} ر.ي\n\n"
        f"الرجاء تحويل المبلغ إلى حساب التاجر في الكريمي وإرسال صورة الإيصال هنا."
    )
    await update.message.reply_text(summary)
    return AWAIT_RECEIPT

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ensure a photo was sent
    if not update.message.photo:
        await update.message.reply_text('الرجاء إرسال صورة الإيصال كملف صورة.')
        return AWAIT_RECEIPT

    photo = update.message.photo[-1]
    file = await photo.get_file()

    # prepare temp paths
    os.makedirs(TEMP_PDF_DIR, exist_ok=True)
    tmp_receipt_path = os.path.join(TEMP_PDF_DIR, f"receipt_{uuid.uuid4().hex}.jpg")

    await file.download_to_drive(tmp_receipt_path)

    # verify payment (simulate)
    amount = REQUIRED_YER_AMOUNT
    verified = await verify_kuraimi_payment(amount=amount, receipt_file_path=tmp_receipt_path)

    if not verified:
        await update.message.reply_text('لم نتمكن من التحقق من الدفع. الرجاء المحاولة أو الاتصال بالدعم.')
        try:
            os.remove(tmp_receipt_path)
        except Exception:
            pass
        return ConversationHandler.END

    # Upload receipt to Supabase Storage
    try:
        user_id = update.message.from_user.id
        filename = os.path.basename(tmp_receipt_path)
        object_name = f"{user_id}/{filename}"
        receipt_url = upload_receipt(tmp_receipt_path, object_name)
    except Exception as e:
        logging.exception('Failed to upload receipt to storage')
        await update.message.reply_text('حدث خطأ أثناء رفع الإيصال. الرجاء المحاولة لاحقًا.')
        try:
            os.remove(tmp_receipt_path)
        except Exception:
            pass
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
        'receipt_url': receipt_url
    }

    db = DBService()
    try:
        db.init_db()
        db.save_sick_leave(record)
    except Exception:
        logging.exception('Failed to save record to DB')
        await update.message.reply_text('حدث خطأ أثناء حفظ السجل في قاعدة البيانات.')
        return ConversationHandler.END
    finally:
        db.close()

    # generate pdf
    try:
        pdf_path = generate_sick_leave_pdf({
            'patient_name': record['patient_name'],
            'duration': record['duration'],
            'uuid': leave_uuid,
            'amount': amount
        })

        # send pdf to user
        await update.message.reply_document(open(pdf_path, 'rb'))
    except Exception:
        logging.exception('Failed to generate/send PDF')
        await update.message.reply_text('حدث خطأ أثناء إنشاء أو إرسال ملف الإجازة.')
    finally:
        # cleanup tmp files
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception:
            pass
        try:
            if os.path.exists(tmp_receipt_path):
                os.remove(tmp_receipt_path)
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
            AWAIT_RECEIPT: [MessageHandler(filters.PHOTO | filters.Document.IMAGE, receipt_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv)

    app.run_polling()

if __name__ == '__main__':
    main()
