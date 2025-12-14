from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_DB_HOST = os.getenv("DB_HOST", "localhost").strip()
_DB_PORT = int(os.getenv("DB_PORT", "3306").strip())
_DB_USER = os.getenv("DB_USER", "root").strip()
_DB_PASSWORD = os.getenv("DB_PASSWORD", "").strip()
_DB_NAME = os.getenv("DB_NAME", "chatbot").strip()

# Use SQLAlchemy URL builder to properly escape credentials
DATABASE_URL = URL.create(
	"mysql+aiomysql",
	username=_DB_USER or None,
	password=_DB_PASSWORD or None,
	host=_DB_HOST or None,
	port=_DB_PORT,
	database=_DB_NAME or None,
	query={"charset": "utf8mb4"},
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
	async with SessionLocal() as session:
		yield session 