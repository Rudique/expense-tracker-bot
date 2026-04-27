import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "app.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("DELETE FROM transactions")
conn.commit()
print(f"Deleted {cur.rowcount} transactions.")
conn.close()
