"""
import psycopg2
from psycopg2.extras import RealDictCursor
from config import SUPABASE_DB_HOST, SUPABASE_DB_PORT, SUPABASE_DB_NAME, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD

CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS sick_leaves (
    id UUID PRIMARY KEY,
    user_id BIGINT,
    patient_name TEXT,
    duration TEXT,
    amount INTEGER,
    payment_status TEXT,
    receipt_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
'''

class DBService:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=SUPABASE_DB_HOST,
            port=SUPABASE_DB_PORT,
            dbname=SUPABASE_DB_NAME,
            user=SUPABASE_DB_USER,
            password=SUPABASE_DB_PASSWORD
        )
        self.conn.autocommit = True

    def init_db(self):
        with self.conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)

    def save_sick_leave(self, record):
        sql = '''
        INSERT INTO sick_leaves (id, user_id, patient_name, duration, amount, payment_status, receipt_url)
        VALUES (%(id)s, %(user_id)s, %(patient_name)s, %(duration)s, %(amount)s, %(payment_status)s, %(receipt_url)s)
        '''
        with self.conn.cursor() as cur:
            cur.execute(sql, record)

    def close(self):
        self.conn.close()
"""
