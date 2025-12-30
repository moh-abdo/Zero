"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Postgres / Supabase connection
SUPABASE_DB_HOST = os.getenv('SUPABASE_DB_HOST')
SUPABASE_DB_PORT = int(os.getenv('SUPABASE_DB_PORT', '5432'))
SUPABASE_DB_NAME = os.getenv('SUPABASE_DB_NAME')
SUPABASE_DB_USER = os.getenv('SUPABASE_DB_USER')
SUPABASE_DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD')

# Payment
KURAIMI_API_KEY = os.getenv('KURAIMI_API_KEY')

# PDF
TEMP_PDF_DIR = os.getenv('TEMP_PDF_DIR', '/tmp')

# Business constants
SAR_TO_YER_RATE = int(os.getenv('SAR_TO_YER_RATE', '420'))
REQUIRED_YER_AMOUNT = int(os.getenv('REQUIRED_YER_AMOUNT', str(10 * SAR_TO_YER_RATE)))
"""
