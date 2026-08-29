import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config
import logging

logger = logging.getLogger(__name__)

class DBClient:
    def __init__(self):
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                dbname=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                cursor_factory=RealDictCursor
            )
            # Read-only configuration recommended at the connection level for safety.
            # However, read-only session prevents DML/DDL but allows selects.
            self.conn.set_session(readonly=True, autocommit=True)
            logger.info("Successfully connected to the database in read-only mode.")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def fetch_all(self, query, params=None):
        if not self.conn or self.conn.closed:
            self.connect()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
            
    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Database connection closed.")
