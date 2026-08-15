import aiosqlite
import os
from pathlib import Path
from .config import get_settings

DB_PATH: str | None = None


def get_db_path() -> str:
    global DB_PATH
    if DB_PATH is None:
        settings = get_settings()
        DB_PATH = settings.db_path
    return DB_PATH


async def get_db() -> aiosqlite.Connection:
    """Get a database connection. Use as async context manager or dependency."""
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def run_migrations():
    """Run all SQL migration files in order."""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    db = await get_db()
    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

        # Get already-applied migrations
        cursor = await db.execute("SELECT filename FROM _migrations")
        applied = {row[0] for row in await cursor.fetchall()}

        # Run pending migrations in order
        migration_files = sorted(f for f in os.listdir(migrations_dir) if f.endswith(".sql"))
        for filename in migration_files:
            if filename not in applied:
                sql = (migrations_dir / filename).read_text()
                await db.executescript(sql)
                await db.execute("INSERT INTO _migrations (filename) VALUES (?)", (filename,))
                await db.commit()
                print(f"Applied migration: {filename}")
    finally:
        await db.close()
