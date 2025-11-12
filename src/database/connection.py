"""
Database connection and utilities for X-Factor
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import time

from src.config.settings import settings
from src.utils.logger import logger


class DatabaseConnection:
    """PostgreSQL database connection manager with connection pooling"""
    
    def __init__(self, min_conn: int = 1, max_conn: int = 10):
        self.connection_pool: Optional[pool.SimpleConnectionPool] = None
        self.min_conn = min_conn
        self.max_conn = max_conn
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                self.min_conn,
                self.max_conn,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD,
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                database=settings.DATABASE_NAME,
                cursor_factory=RealDictCursor
            )
            logger.info(f"Database connection pool initialized (min={self.min_conn}, max={self.max_conn})")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool (context manager)"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
        """Get a cursor (context manager)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database cursor error: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """Execute a query and optionally fetch results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None
    
    def execute_many(self, query: str, data: List[tuple]) -> int:
        """Execute a query with multiple parameter sets"""
        with self.get_cursor() as cursor:
            cursor.executemany(query, data)
            return cursor.rowcount
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("All database connections closed")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            result = self.execute_query("SELECT 1 as test")
            return result[0]['test'] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    

# Global database connection instance
db = DatabaseConnection()


def wait_for_db(max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for database to be ready"""
    for i in range(max_retries):
        try:
            if db.test_connection():
                logger.info("Database is ready")
                return True
        except Exception as e:
            logger.debug(f"Waiting for database... ({i+1}/{max_retries})")
        time.sleep(delay)
    
    logger.error("Database connection timeout")
    return False


def init_db():
    """Initialize database (apply schema)"""
    logger.info("Initializing database...")
    
    # Check if database is ready
    if not wait_for_db():
        raise Exception("Database is not available")
    
    logger.info("Database initialization complete")
    return True


# Cleanup on exit
import atexit
atexit.register(db.close_all_connections)
