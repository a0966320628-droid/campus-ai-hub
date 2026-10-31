"""Consistent SQLite backup plus attachment archive, never modifies source."""
import hashlib, json, sqlite3, tarfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "campus_ai.db"
if not source.is_file():
    raise SystemExit("SQLite file missing; use pg_dump for Render PostgreSQL")
backup = ROOT / "backups" / time.strftime("%Y%m%d_%H%M%S")
backup.mkdir(parents=True, exist_ok=False)
with sqlite3.connect(str(source)) as src, sqlite3.connect(str(backup / "campus_ai.db")) as dest:
    src.backup(dest)
with sqlite3.connect(str(backup / "campus_ai.db")) as c:
    result = c.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok": raise SystemExit("Backup integrity check failed: " + result)
    counts = {name: c.execute('SELECT COUNT(*) FROM "'+name+'"').fetchone()[0] for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
uploads = ROOT / "static" / "uploads"
if uploads.exists():
    with tarfile.open(backup / "uploads.tar.gz", "w:gz") as tar: tar.add(uploads, arcname="uploads")
checksums = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in backup.iterdir() if f.is_file()}
(backup / "manifest.json").write_text(json.dumps({"integrity":result,"counts":counts,"sha256":checksums},ensure_ascii=False,indent=2),encoding="utf-8")
print("Backup verified:", backup)
