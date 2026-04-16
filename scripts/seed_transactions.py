"""Generate 500 random transactions spread across the last 12 months."""

import random
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "app.db"

# Realistic amount ranges per category name keyword
AMOUNT_HINTS = {
    "food":      (50, 2000),
    "grocery":   (200, 5000),
    "cafe":      (100, 800),
    "coffee":    (80, 400),
    "transport": (50, 500),
    "taxi":      (100, 1500),
    "health":    (200, 5000),
    "sport":     (300, 3000),
    "entertain": (200, 3000),
    "cinema":    (300, 900),
    "cloth":     (500, 8000),
    "shop":      (300, 5000),
    "subscript": (99, 999),
    "travel":    (1000, 15000),
    "utility":   (500, 4000),
    "bill":      (500, 4000),
}

COMMENTS = [
    "lunch", "dinner", "breakfast", "weekly shop", "online order",
    "with friends", "spontaneous", "planned", "monthly payment",
    None, None, None,  # more Nones → most tx have no comment
]


def amount_for(category_name: str) -> float:
    name_lower = category_name.lower()
    for keyword, (lo, hi) in AMOUNT_HINTS.items():
        if keyword in name_lower:
            return round(random.uniform(lo, hi), 2)
    return round(random.uniform(100, 3000), 2)


def random_dt(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    users = cur.execute("SELECT id FROM users").fetchall()
    categories = cur.execute("SELECT id, name FROM categories").fetchall()

    if not users:
        print("No users found — run the bot first to register at least one user.")
        return
    if not categories:
        print("No categories found — add categories via /add_category first.")
        return

    print(f"Found {len(users)} user(s) and {len(categories)} categor(ies).")

    end_dt   = datetime.now()
    start_dt = end_dt - timedelta(days=365)

    rows = []
    for _ in range(500):
        user_id     = random.choice(users)[0]
        cat_id, cat_name = random.choice(categories)
        amount      = amount_for(cat_name)
        comment     = random.choice(COMMENTS)
        is_shared   = random.random() < 0.2  # 20% shared
        created_at  = random_dt(start_dt, end_dt).strftime("%Y-%m-%d %H:%M:%S")
        rows.append((user_id, amount, cat_id, comment, int(is_shared), created_at, created_at))

    cur.executemany(
        """
        INSERT INTO transactions (user_id, amount, category_id, comment, is_shared, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()
    print(f"Inserted {len(rows)} transactions. Done.")


if __name__ == "__main__":
    main()
