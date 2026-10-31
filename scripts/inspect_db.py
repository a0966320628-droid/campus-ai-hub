import sqlite3
from pathlib import Path
db=Path(__file__).resolve().parents[1]/"campus_ai.db"
with sqlite3.connect(str(db)) as c:
    print("integrity:",c.execute("PRAGMA integrity_check").fetchone()[0])
    for (table,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        print(table,c.execute('SELECT COUNT(*) FROM "'+table+'"').fetchone()[0])
