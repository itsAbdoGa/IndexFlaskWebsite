from contextlib import contextmanager
import psycopg2

DATABASE_URL = "postgresql://postgres.yssyseltnmmdkrhczfnr:legoproductlookup1@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Database Connected ")
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise  
    finally:
        if conn:
            conn.close()

                
    