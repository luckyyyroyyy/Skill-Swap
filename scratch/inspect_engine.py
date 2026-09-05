import sys
from app import app, db
import sqlite3

with app.app_context():
    url_str = str(db.engine.url)
    sys.stdout.buffer.write(f"Engine URL: {url_str}\n".encode('utf-8'))
    db_file = db.engine.url.database
    sys.stdout.buffer.write(f"Database file: {db_file}\n".encode('utf-8'))
    
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    sys.stdout.buffer.write(f"Tables: {tables}\n".encode('utf-8'))
    conn.close()
