import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR   = Path(__file__).resolve().parent.parent
SERVER_DB  = Path("N:/memory/noctis_memory.db")
LOCAL_DB   = BASE_DIR / "logs" / "offline_cache" / "noctis_memory_offline.db"
SYNC_FLAG  = BASE_DIR / "logs" / "offline_cache" / ".needs_sync"

LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)

def _server_available() -> bool:
    try:
        test_file = SERVER_DB.parent / ".ping"
        test_file.touch()
        test_file.unlink()
        return True
    except Exception:
        return False

def _get_db_path() -> Path:
    if _server_available():
        return SERVER_DB
    else:
        SYNC_FLAG.touch()
        return LOCAL_DB

def _get_conn() -> sqlite3.Connection:
    path = _get_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn

# ── Schema ────────────────────────────────────────────────────
def init_db():
    for path in [SERVER_DB, LOCAL_DB]:
        try:
            if path == LOCAL_DB or _server_available():
                path.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(str(path))
                cur = conn.cursor()
                cur.executescript("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id         INTEGER PRIMARY KEY AUTOINCREMENT,
                        started_at TEXT NOT NULL,
                        ended_at   TEXT,
                        mode       TEXT
                    );
                    CREATE TABLE IF NOT EXISTS messages (
                        id         INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        role       TEXT NOT NULL,
                        content    TEXT NOT NULL,
                        timestamp  TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS facts (
                        id         INTEGER PRIMARY KEY AUTOINCREMENT,
                        key        TEXT UNIQUE NOT NULL,
                        value      TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS preferences (
                        id         INTEGER PRIMARY KEY AUTOINCREMENT,
                        key        TEXT UNIQUE NOT NULL,
                        value      TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                """)
                conn.commit()
                conn.close()
        except Exception:
            pass

# ── Sessions ──────────────────────────────────────────────────
def start_session() -> int:
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute("INSERT INTO sessions (started_at) VALUES (?)",
                (datetime.now().isoformat(),))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid

def end_session(session_id: int):
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute("UPDATE sessions SET ended_at=? WHERE id=?",
                (datetime.now().isoformat(), session_id))
    conn.commit()
    conn.close()

# ── Messages ──────────────────────────────────────────────────
def log_message(session_id: int, role: str, content: str):
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?,?,?,?)",
        (session_id, role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_recent_messages(session_id: int, limit: int = 20) -> list:
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute(
        "SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
        (session_id, limit)
    )
    rows = cur.fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

# ── Facts ─────────────────────────────────────────────────────
def save_fact(key: str, value: str):
    _write_both("facts", key, value)

def get_fact(key: str) -> str | None:
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT value FROM facts WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else None

def delete_fact(key: str):
    _delete_both("facts", key)

def get_all_facts() -> dict:
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT key, value FROM facts")
    rows = cur.fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

# ── Preferences ───────────────────────────────────────────────
def save_preference(key: str, value: str):
    _write_both("preferences", key, value)

def get_preference(key: str) -> str | None:
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT value FROM preferences WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else None

def delete_preference(key: str):
    _delete_both("preferences", key)

def get_all_preferences() -> dict:
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT key, value FROM preferences")
    rows = cur.fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

# ── Write to BOTH server and local always ─────────────────────
def _write_both(table: str, key: str, value: str):
    ts = datetime.now().isoformat()
    for path in [SERVER_DB, LOCAL_DB]:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(path))
            cur  = conn.cursor()
            cur.execute(
                f"INSERT INTO {table} (key, value, updated_at) VALUES (?,?,?) "
                f"ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (key, value, ts)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

def _delete_both(table: str, key: str):
    for path in [SERVER_DB, LOCAL_DB]:
        try:
            conn = sqlite3.connect(str(path))
            cur  = conn.cursor()
            cur.execute(f"DELETE FROM {table} WHERE key=?", (key,))
            conn.commit()
            conn.close()
        except Exception:
            pass

# ── Sync offline → server ─────────────────────────────────────
def sync_offline_to_server():
    if not _server_available():
        return
    if not LOCAL_DB.exists():
        return

    try:
        src  = sqlite3.connect(str(LOCAL_DB))
        dst  = sqlite3.connect(str(SERVER_DB))
        scur = src.cursor()
        dcur = dst.cursor()

        # Sync facts (local: updated → server: updated_at)
        scur.execute("SELECT key, value, updated_at FROM facts")
        for key, value, ts in scur.fetchall():
            dcur.execute(
                "INSERT INTO facts (key, value, updated_at) VALUES (?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at "
                "WHERE excluded.updated_at > facts.updated_at",
                (key, value, ts)
            )

        # Sync preferences (local: updated → server: updated_at)
        scur.execute("SELECT key, value, updated_at FROM preferences")
        for key, value, ts in scur.fetchall():
            dcur.execute(
                "INSERT INTO preferences (key, value, updated_at) VALUES (?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at "
                "WHERE excluded.updated_at > preferences.updated_at",
                (key, value, ts)
            )

        # Sync messages
        scur.execute("SELECT session_id, role, content, timestamp FROM messages")
        for session_id, role, content, timestamp in scur.fetchall():
            dcur.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id=? AND role=? AND timestamp=?",
                (session_id, role, timestamp)
            )
            if dcur.fetchone()[0] == 0:
                dcur.execute(
                    "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?,?,?,?)",
                    (session_id, role, content, timestamp)
                )

        dst.commit()
        src.close()
        dst.close()

        if SYNC_FLAG.exists():
            SYNC_FLAG.unlink()

        print("[DB] Offline cache synced to server.")
    except Exception as e:
        print(f"[DB] Sync failed — {e}")

# ── NoctisDB class wrapper (required by test_sync.py and noctis_core.py) ──
class NoctisDB:
    def log_session(self, session_id, model="llama3.2:3b"):
        return start_session()

    def log_message(self, session_id, role, content):
        log_message(session_id, role, content)

    def save_fact(self, key, value):
        save_fact(key, value)

    def get_facts(self, limit=5):
        facts = get_all_facts()
        return list(facts.items())[:limit]

    def save_preference(self, key, value):
        save_preference(key, value)

    def get_preferences(self):
        prefs = get_all_preferences()
        return list(prefs.items())

    def delete_fact(self, key):
        delete_fact(key)

    def delete_preference(self, key):
        delete_preference(key)

    def sync_offline_to_server(self):
        sync_offline_to_server()