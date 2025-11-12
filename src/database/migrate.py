"""
Database migration runner for X-Factor
Runs SQL migration files in order
"""

import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql

from src.config.settings import settings
from src.utils.logger import logger

SCHEMA_DIR = Path(__file__).parent.parent.parent / "schema"


def get_migration_files():
    """Get all schema SQL files in order"""
    if not SCHEMA_DIR.exists():
        logger.error(f"Schema directory not found: {SCHEMA_DIR}")
        return []
    
    migration_files = sorted(SCHEMA_DIR.glob("*.sql"))
    return migration_files


def create_migrations_table(conn):
    """Create table to track applied migrations"""
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT NOW()
            )
        """)
    conn.commit()
    logger.info("Migrations tracking table created")


def get_applied_migrations(conn):
    """Get list of already applied migrations"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT migration_name FROM schema_migrations")
        return {row[0] for row in cursor.fetchall()}


def apply_migration(conn, migration_file: Path):
    """Apply a single migration file"""
    migration_name = migration_file.name
    
    logger.info(f"Applying migration: {migration_name}")
    
    try:
        # Read migration file
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Execute migration
        with conn.cursor() as cursor:
            cursor.execute(sql_content)
            
            # Record migration as applied
            cursor.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES (%s)",
                (migration_name,)
            )
        
        conn.commit()
        logger.info(f"✓ Migration {migration_name} applied successfully")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Failed to apply migration {migration_name}: {e}")
        raise


def init_database(dry_run: bool = False):
    """Run all pending schema SQL files to initialize/reset the database"""
    logger.info("Starting database initialization...")
    
    # Get migration files
    migration_files = get_migration_files()
    if not migration_files:
        logger.warning("No migration files found")
        return
    
    logger.info(f"Found {len(migration_files)} migration file(s)")
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME
        )
        logger.info("Connected to database")
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Create migrations tracking table
        create_migrations_table(conn)
        
        # Get already applied migrations
        applied_migrations = get_applied_migrations(conn)
        logger.info(f"{len(applied_migrations)} migration(s) already applied")
        
        # Apply pending migrations
        pending_migrations = [
            f for f in migration_files 
            if f.name not in applied_migrations
        ]
        
        if not pending_migrations:
            logger.info("No pending migrations")
            return
        
        logger.info(f"Applying {len(pending_migrations)} pending migration(s)...")
        
        if dry_run:
            logger.info("DRY RUN - No migrations will be applied")
            for migration_file in pending_migrations:
                logger.info(f"  Would apply: {migration_file.name}")
            return
        
        # Apply each pending migration
        for migration_file in pending_migrations:
            apply_migration(conn, migration_file)
        
        logger.info("✓ Database initialization complete!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
        
    finally:
        conn.close()


def rollback_migration(migration_name: str):
    """Rollback a specific migration (manual process)"""
    logger.warning(f"Rollback for migration '{migration_name}' must be done manually")
    logger.info("1. Write a rollback SQL script")
    logger.info("2. Execute it manually")
    logger.info("3. Remove entry from schema_migrations table")


def show_migration_status():
    """Show status of all migrations"""
    logger.info("Migration Status")
    logger.info("=" * 60)
    
    try:
        conn = psycopg2.connect(
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME
        )
        
        create_migrations_table(conn)
        applied_migrations = get_applied_migrations(conn)
        conn.close()
        
        migration_files = get_migration_files()
        
        for migration_file in migration_files:
            status = "✓ APPLIED" if migration_file.name in applied_migrations else "○ PENDING"
            logger.info(f"{status}  {migration_file.name}")
        
    except Exception as e:
        logger.error(f"Failed to show migration status: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="X-Factor Database Migration Tool")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be applied without applying")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    
    args = parser.parse_args()
    
    if args.status:
        show_migration_status()
    else:
        init_database(dry_run=args.dry_run)
