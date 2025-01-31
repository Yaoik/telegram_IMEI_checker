import psycopg2.pool
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

db_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port="5432",
    database=os.getenv("DB_NAME")
)

def get_db_connection():
    return db_pool.getconn()

def release_db_connection(conn):
    db_pool.putconn(conn)

def is_user_in_whitelist(id: int) -> bool:
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT EXISTS(SELECT 1 FROM users_whitelist WHERE user_id = %s)", [id])
        exists = cursor.fetchone()[0]
        return exists
    except Exception as e:
        logger.error(f"Error occurred during checking user whitelist: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db_connection(conn)

def verify_token(token: str) -> bool:
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM tokens WHERE token = %s)",
            [token]
        )
        exists = cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        exists = False
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db_connection(conn)
    return exists

def initialize_db():
    """Функция для создания таблиц, если они не существуют"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                token VARCHAR(255) PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_whitelist (
                user_id BIGINT PRIMARY KEY
            )
        """)
        
        cursor.execute("DELETE FROM users_whitelist")
        cursor.execute("DELETE FROM tokens")
        
        tg_whitelist_ids = os.getenv('TG_ID_WHITELIST')
        if tg_whitelist_ids:
            tg_whitelist_ids = tg_whitelist_ids.split(',')
            for user_id in tg_whitelist_ids:
                cursor.execute("""
                    INSERT INTO users_whitelist (user_id)
                    VALUES (%s)
                    ON CONFLICT (user_id) DO NOTHING
                """, [user_id])
        
        tokens = os.getenv('TOKENS')
        if tokens:
            tokens = tokens.split(',')
            for token in tokens:
                cursor.execute("""
                    INSERT INTO tokens (token)
                    VALUES (%s)
                    ON CONFLICT (token) DO NOTHING
                """, [token])
                
        conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error occurred during DB initialization: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db_connection(conn)