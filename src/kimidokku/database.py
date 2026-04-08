"""Database connection and initialization."""

import asyncio
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

import aiosqlite

from kimidokku.config import get_settings


class Database:
    """Database connection manager."""

    _instance: Optional["Database"] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> "Database":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._db_path: Optional[Path] = None
        self._initialized = True

    async def initialize(self, db_path: Path | str) -> None:
        """Initialize database connection pool."""
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        await self._init_schema()

    async def _init_schema(self) -> None:
        """Initialize database schema from SQL file."""
        if not self._db_path:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        schema_path = Path(__file__).parent / "db_schema.sql"
        schema_sql = schema_path.read_text()

        async with aiosqlite.connect(self._db_path) as db:
            # Enable foreign keys
            await db.execute("PRAGMA foreign_keys = ON")
            # Enable regex support
            await db.execute("PRAGMA case_sensitive_like = OFF")
            # Split and execute each statement
            for statement in schema_sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    await db.execute(stmt)
            await db.commit()

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get database connection."""
        if not self._db_path:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            yield db

    async def execute(self, query: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """Execute a query."""
        async with self.get_connection() as db:
            cursor = await db.execute(query, parameters)
            await db.commit()
            return cursor

    async def fetch_one(self, query: str, parameters: tuple = ()) -> Optional[dict]:
        """Fetch a single row."""
        async with self.get_connection() as db:
            cursor = await db.execute(query, parameters)
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetch_all(self, query: str, parameters: tuple = ()) -> list[dict]:
        """Fetch all rows."""
        async with self.get_connection() as db:
            cursor = await db.execute(query, parameters)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# Global database instance
db = Database()


async def init_database() -> None:
    """Initialize database on application startup."""
    settings = get_settings()
    await db.initialize(settings.db_path)
