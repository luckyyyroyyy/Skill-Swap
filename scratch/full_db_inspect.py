import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = os.path.abspath("instance/skillswap.db")
print("Absolute path:", db_path)

print("File size:", os.path.getsize(db_path))

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [r[0] for r in cur.fetchall()]
print(f"\nTotal tables found: {len(tables)}")
for t in tables:
    cur.execute(f"PRAGMA table_info('{t}');")
    cols = [c[1] for c in cur.fetchall()]
    cur.execute(f"SELECT COUNT(*) FROM '{t}';")
    count = cur.fetchone()[0]
    print(f"  * {t} ({count} rows) -> Columns: {', '.join(cols[:5])}{'...' if len(cols)>5 else ''}")

conn.close()
