from pathlib import Path
def test_required_files():
    root=Path(__file__).resolve().parents[1]
    for path in ("app.py", "models/ai.py", "routes/health.py", "scripts/backup_local.py"):
        assert (root/path).is_file()
