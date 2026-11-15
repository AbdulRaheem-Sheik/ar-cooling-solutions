"""The site's content database (SQLite, built into Python: no server to run).

Each JSON file under data/ is one row in the `records` table, so a record keeps exactly
the shape it had as a file and every template works unchanged:

    collection   name                 data
    products     01-split-ac-units    {...the file's JSON...}
    spares       01-copper-coils      {...}
    site         featured-spare       {...}
    home         faqs                 {...}

The database is a single file, instance/ar_cooling.db by default (AR_DATABASE_PATH changes
it; on a host, point it at the persistent disk). When it is empty, it is filled from data/
on first use, so a fresh server sets itself up. Every admin save keeps the previous version
in `record_history`, so a mistake can be undone.

    python store.py import            # fill an empty database from data/
    python store.py import --replace  # overwrite the database with data/ (loses admin edits)
    python store.py export            # write the database back to data/ (to commit to git)
    python store.py history <collection> <name>
    python store.py restore <collection> <name> <version-id>
"""

import json
import os
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = BASE_DIR / "instance" / "ar_cooling.db"

# collection -> (folder under data/, files that belong to another collection)
FOLDER_COLLECTIONS = {
    "products": ("products", ()),
    "services": ("services", ()),
    "spares": ("spares", ("featured-spare.json",)),
    "compressors": ("compressors", ()),
    "home": ("home", ()),
}
# Single files kept in the "site" collection: name -> path under data/
SITE_FILES = {"featured-spare": Path("spares") / "featured-spare.json"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    collection TEXT NOT NULL,
    name       TEXT NOT NULL,
    position   INTEGER NOT NULL,
    data       TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (collection, name)
);
CREATE TABLE IF NOT EXISTS record_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    collection TEXT NOT NULL,
    name       TEXT NOT NULL,
    data       TEXT NOT NULL,
    saved_at   TEXT NOT NULL
);
"""

_ready = set()   # database paths already created and seeded in this process


def db_path():
    return Path(os.environ.get("AR_DATABASE_PATH") or DEFAULT_DB_PATH)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    """A connection to the database, creating and seeding it on first use."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    if path not in _ready:
        conn.execute("PRAGMA journal_mode=WAL")   # readers don't wait while the admin saves
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 0:
            _import(conn, replace=False)
        conn.commit()
        _ready.add(path)
    return conn


def _seed_files():
    """(collection, name, position, path) for every content file under data/."""
    for collection, (folder, excluded) in FOLDER_COLLECTIONS.items():
        files = [f for f in sorted((DATA_DIR / folder).glob("*.json")) if f.name not in excluded]
        for position, file_path in enumerate(files):
            yield collection, file_path.stem, position, file_path
    for position, (name, rel_path) in enumerate(SITE_FILES.items()):
        yield "site", name, position, DATA_DIR / rel_path


def _import(conn, replace):
    count = 0
    if replace:
        conn.execute("DELETE FROM records")
    for collection, name, position, file_path in _seed_files():
        data = json.loads(file_path.read_text(encoding="utf-8"))
        cursor = conn.execute(
            "INSERT OR IGNORE INTO records (collection, name, position, data, updated_at) VALUES (?, ?, ?, ?, ?)",
            (collection, name, position, json.dumps(data, ensure_ascii=False), _now()),
        )
        count += cursor.rowcount
    return count   # records added


def all_records(collection):
    """Every record in a collection, in order, as fresh dicts (safe to modify)."""
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT data FROM records WHERE collection = ? ORDER BY position, name", (collection,)
        ).fetchall()
    return tuple(json.loads(row["data"]) for row in rows)


def get_record(collection, name):
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT data FROM records WHERE collection = ? AND name = ?", (collection, name)
        ).fetchone()
    return json.loads(row["data"]) if row else None


def find_name(collection, name_or_slug):
    """The record name for a name (e.g. 01-copper-coils) or a record's slug (copper-coils)."""
    with closing(connect()) as conn:
        rows = conn.execute("SELECT name, data FROM records WHERE collection = ?", (collection,)).fetchall()
    for row in rows:
        if row["name"] == name_or_slug:
            return row["name"]
    for row in rows:
        if json.loads(row["data"]).get("slug") == name_or_slug:
            return row["name"]
    return None


def save_record(collection, name, data):
    """Replace a record, keeping its previous version in record_history."""
    with closing(connect()) as conn, conn:
        old = conn.execute(
            "SELECT data FROM records WHERE collection = ? AND name = ?", (collection, name)
        ).fetchone()
        if old is None:
            raise KeyError(f"{collection}/{name} does not exist")
        conn.execute(
            "INSERT INTO record_history (collection, name, data, saved_at) VALUES (?, ?, ?, ?)",
            (collection, name, old["data"], _now()),
        )
        conn.execute(
            "UPDATE records SET data = ?, updated_at = ? WHERE collection = ? AND name = ?",
            (json.dumps(data, ensure_ascii=False), _now(), collection, name),
        )


def history(collection, name):
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT id, saved_at FROM record_history WHERE collection = ? AND name = ? ORDER BY id DESC",
            (collection, name),
        ).fetchall()


def restore(collection, name, version_id):
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT data FROM record_history WHERE id = ? AND collection = ? AND name = ?",
            (version_id, collection, name),
        ).fetchone()
    if row is None:
        raise KeyError(f"No saved version {version_id} for {collection}/{name}")
    save_record(collection, name, json.loads(row["data"]))


def export_to_files():
    """Write records back to their JSON files under data/ (same layout as before).

    Only records whose content differs from their file are written, so files nobody
    edited keep their hand-tidied formatting and git shows just the real changes."""
    paths = {(collection, name): path for collection, name, _, path in _seed_files()}
    count = 0
    with closing(connect()) as conn:
        rows = conn.execute("SELECT collection, name, data FROM records").fetchall()
    for row in rows:
        if row["collection"] == "site":
            path = DATA_DIR / SITE_FILES[row["name"]]
        else:
            path = paths.get((row["collection"], row["name"])) or (
                DATA_DIR / FOLDER_COLLECTIONS[row["collection"]][0] / f"{row['name']}.json")
        data = json.loads(row["data"])
        if path.exists() and json.loads(path.read_text(encoding="utf-8")) == data:
            continue
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        path.write_bytes(text.encode("utf-8"))   # bytes: keep \n line endings on Windows too
        count += 1
    return count   # files written


def main(argv):
    usage = __doc__.split("\n\n")[-1]
    if not argv:
        print(usage)
        return 1
    command, args = argv[0], argv[1:]
    if command == "import":
        with closing(connect()) as conn, conn:
            count = _import(conn, replace="--replace" in args)
        print(f"{'Replaced with' if '--replace' in args else 'Added'} {count} records in {db_path()}")
    elif command == "export":
        print(f"Updated {export_to_files()} changed files in {DATA_DIR}")
    elif command == "history" and len(args) == 2:
        for row in history(*args):
            print(f"{row['id']:>5}  {row['saved_at']}")
    elif command == "restore" and len(args) == 3:
        restore(args[0], args[1], int(args[2]))
        print(f"Restored {args[0]}/{args[1]} to version {args[2]}")
    else:
        print(usage)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
