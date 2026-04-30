"""
Migrate data from SQLite (app.db) → PostgreSQL.

Usage:
    python scripts/migrate_to_pg.py

Expects both DB_URL (postgres) in .env and a SQLITE_URL override or
reads directly from app.db in the project root.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Make sure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

import aiosqlite
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DT_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f")


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in DT_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


BOOL_FIELDS = {"is_shared", "is_active"}


def fix_row(row: dict) -> dict:
    """Convert datetime strings and int booleans to proper Python types."""
    row = dict(row)
    row["created_at"] = parse_dt(row.get("created_at"))
    row["updated_at"] = parse_dt(row.get("updated_at"))
    for field in BOOL_FIELDS:
        if field in row and row[field] is not None:
            row[field] = bool(row[field])
    return row


def fix_timestamps(rows: list[dict]) -> list[dict]:
    return [fix_row(r) for r in rows]

PG_URL = os.environ.get(
    "PG_URL",
    "postgresql+asyncpg://bot:secret@localhost:5432/expense_bot",
)
SQLITE_PATH = Path(__file__).parent.parent / "app.db"


async def fetch_all(sqlite_db: aiosqlite.Connection, query: str) -> list[dict]:
    sqlite_db.row_factory = aiosqlite.Row
    async with sqlite_db.execute(query) as cursor:
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def migrate() -> None:
    if not SQLITE_PATH.exists():
        print(f"SQLite file not found: {SQLITE_PATH}")
        sys.exit(1)

    print(f"Source : {SQLITE_PATH}")
    print(f"Target : {PG_URL}")
    print()

    engine = create_async_engine(PG_URL, echo=False)

    async with aiosqlite.connect(SQLITE_PATH) as db:
        users = fix_timestamps(await fetch_all(db, "SELECT * FROM users ORDER BY id"))
        categories = fix_timestamps(await fetch_all(db, "SELECT * FROM categories ORDER BY id"))
        transactions = fix_timestamps(await fetch_all(db, "SELECT * FROM transactions ORDER BY id"))
        groups = fix_timestamps(await fetch_all(db, "SELECT * FROM groups ORDER BY id"))
        reminders = fix_timestamps(await fetch_all(db, "SELECT * FROM reminders ORDER BY id"))

    print(f"  users        : {len(users)}")
    print(f"  categories   : {len(categories)}")
    print(f"  transactions : {len(transactions)}")
    print(f"  groups       : {len(groups)}")
    print(f"  reminders    : {len(reminders)}")
    print()

    async with engine.begin() as conn:
        # ── users ──────────────────────────────────────────────────────────
        if users:
            await conn.execute(
                text(
                    "INSERT INTO users (id, telegram_id, username, first_name, last_name, created_at, updated_at) "
                    "VALUES (:id, :telegram_id, :username, :first_name, :last_name, :created_at, :updated_at) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                users,
            )
            max_id = max(r["id"] for r in users)
            await conn.execute(text(f"SELECT setval('users_id_seq', {max_id})"))
            print(f"  users inserted, sequence reset to {max_id}")

        # ── categories ─────────────────────────────────────────────────────
        if categories:
            await conn.execute(
                text(
                    "INSERT INTO categories (id, name, emoji, created_at, updated_at) "
                    "VALUES (:id, :name, :emoji, :created_at, :updated_at) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                categories,
            )
            max_id = max(r["id"] for r in categories)
            await conn.execute(text(f"SELECT setval('categories_id_seq', {max_id})"))
            print(f"  categories inserted, sequence reset to {max_id}")

        # ── transactions ───────────────────────────────────────────────────
        if transactions:
            await conn.execute(
                text(
                    "INSERT INTO transactions (id, user_id, amount, category_id, comment, is_shared, created_at, updated_at) "
                    "VALUES (:id, :user_id, :amount, :category_id, :comment, :is_shared, :created_at, :updated_at) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                transactions,
            )
            max_id = max(r["id"] for r in transactions)
            await conn.execute(text(f"SELECT setval('transactions_id_seq', {max_id})"))
            print(f"  transactions inserted, sequence reset to {max_id}")

        # ── groups ─────────────────────────────────────────────────────────
        if groups:
            await conn.execute(
                text(
                    "INSERT INTO groups (id, chat_id, title, reminders_thread_id, created_at, updated_at) "
                    "VALUES (:id, :chat_id, :title, :reminders_thread_id, :created_at, :updated_at) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                groups,
            )
            max_id = max(r["id"] for r in groups)
            await conn.execute(text(f"SELECT setval('groups_id_seq', {max_id})"))
            print(f"  groups inserted, sequence reset to {max_id}")

        # ── reminders ──────────────────────────────────────────────────────
        if reminders:
            await conn.execute(
                text(
                    "INSERT INTO reminders "
                    "(id, user_id, telegram_user_id, title, schedule_type, schedule_value, "
                    "send_time, target, chat_id, thread_id, is_active, created_at, updated_at) "
                    "VALUES (:id, :user_id, :telegram_user_id, :title, :schedule_type, :schedule_value, "
                    ":send_time, :target, :chat_id, :thread_id, :is_active, :created_at, :updated_at) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                reminders,
            )
            max_id = max(r["id"] for r in reminders)
            await conn.execute(text(f"SELECT setval('reminders_id_seq', {max_id})"))
            print(f"  reminders inserted, sequence reset to {max_id}")

    await engine.dispose()
    print()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(migrate())
