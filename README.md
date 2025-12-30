"""
````markdown name=README.md
# Sick Leave Bot (Telegram)

بوت تليجرام لإنشاء إجازات مرضية مع توليد PDF وباركود، مع عملية دفع محاكية عبر الكريمي.

## المتطلبات
- Python 3.10+

## الإعداد
1. انسخ `.env.sample` إلى `.env` واملأ القيم.
2. ثبت المتطلبات:
```
pip install -r requirements.txt
```
3. ضع ملف خط يدعم العربية `DejaVuSans.ttf` في جذر المشروع أو عدل `FONT_FILE` في `pdf_generator.py` ليشير إلى خط عربي.
4. شغّل البوت:
```
python main.py
```

## ملاحظات
- دالة التحقق من الدفع `verify_kuraimi_payment` محاكية، يجب ربطها لاحقًا بواجهة الكريمي الحقيقية.
- تأكد من إعداد اتصال PostgreSQL (Supabase) وتعبئة متغيرات الاتصال في `.env`.
````
"""
