import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

excuses = [
    "عذرًا، المريض يعاني من نزلة برد ويحتاج إلى الراحة لمدة يومين.",
    "عذرًا، المريض بحاجة لإجازة بسبب ارتفاع درجة الحرارة الحاد.",
    "عذر طبي: ينصح بالراحة لمدة 3 أيام نظراً لالتهاب الحلق.",
    "عذر طبي: المريض يعاني من ألم في الظهر ويحتاج إلى راحة تامة ليومين.",
    "عذر طبي: يفضل تجنب الإجهاد لمدة خمسة أيام نتيجة لإصابة رياضية."
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا بك في بوت الأعذار الطبية! أرسل /excuse للحصول على عذر طبي."
    )

async def excuse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from random import choice
    await update.message.reply_text(choice(excuses))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    TOKEN = "8322006109:AAEQ-rd1VqQoSk3UH9Kk3V500wAP87AFvDg"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("excuse", excuse))

    app.run_polling()
