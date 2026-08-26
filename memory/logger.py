"""
DevilCore — Noctis Memory System
memory/logger.py — Auto-logging with offline fallback
Online  → writes to N:\memory\ (Linux server)
Offline → writes to C:\DevilCore\logs\offline_cache\ (local)
Sync    → auto-syncs cache to server when it comes back
"""

import os
import shutil
import sqlite3
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────
SERVER_DB     = r"N:\memory\noctis_memory.db"
SERVER_LOG    = r"N:\logs\noctis_sessions.log"
SERVER_AVAIL  = r"N:\memory"

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_CACHE   = os.path.join(BASE_DIR, "logs", "offline_cache")
LOCAL_DB      = os.path.join(LOCAL_CACHE, "noctis_memory_offline.db")
LOCAL_LOG     = os.path.join(LOCAL_CACHE, "noctis_sessions_offline.log")

def server_online() -> bool:
    """Check if N:\ memory server is reachable."""
    try:
        return os.path.isdir(SERVER_AVAIL)
    except Exception:
        return False

def get_db_path() -> str:
    return SERVER_DB if server_online() else LOCAL_DB

def get_log_path() -> str:
    return SERVER_LOG if server_online() else LOCAL_LOG

# ── DB init ───────────────────────────────────────────────────────
def init_db(db_path: str = None):
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at  TEXT NOT NULL,
            ended_at    TEXT,
            mode        TEXT DEFAULT 'terminal'
        );
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
        CREATE TABLE IF NOT EXISTS facts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            key         TEXT NOT NULL UNIQUE,
            value       TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS preferences (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            key         TEXT NOT NULL UNIQUE,
            value       TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

# ── Sync offline cache to server ──────────────────────────────────
def sync_offline_cache():
    """
    Called on startup. If server is online and offline cache has data,
    merge it into the server DB then clear the cache.
    """
    if not server_online():
        return
    if not os.path.exists(LOCAL_DB):
        return

    print("[Memory] Server online — syncing offline cache to N:\\memory\\...")
    try:
        # Attach offline DB to server DB and merge all tables
        server_conn = sqlite3.connect(SERVER_DB)
        server_conn.execute(f"ATTACH DATABASE '{LOCAL_DB}' AS offline")

        server_conn.executescript("""
            INSERT OR IGNORE INTO main.sessions
                SELECT * FROM offline.sessions;

            INSERT OR IGNORE INTO main.messages
                SELECT * FROM offline.messages;

            INSERT OR REPLACE INTO main.facts
                SELECT * FROM offline.facts;

            INSERT OR REPLACE INTO main.preferences
                SELECT * FROM offline.preferences;
        """)
        server_conn.commit()
        server_conn.close()

        # Merge offline log into server log
        if os.path.exists(LOCAL_LOG):
            with open(LOCAL_LOG, "r", encoding="utf-8") as f:
                cached_logs = f.read()
            with open(SERVER_LOG, "a", encoding="utf-8") as f:
                f.write(f"\n[SYNCED FROM OFFLINE CACHE]\n{cached_logs}")

        # Clear offline cache after successful sync
        os.remove(LOCAL_DB)
        if os.path.exists(LOCAL_LOG):
            os.remove(LOCAL_LOG)

        print("[Memory] Offline cache synced and cleared.")

    except Exception as e:
        print(f"[Memory] Sync error: {e}")


# ── Logger class ──────────────────────────────────────────────────
class NoctisLogger:
    def __init__(self, mode: str = "terminal"):
        os.makedirs(LOCAL_CACHE, exist_ok=True)

        # Try to sync any offline data first
        sync_offline_cache()

        self.mode       = mode
        self.db_path    = get_db_path()
        self.log_path   = get_log_path()
        self.online     = server_online()

        init_db(self.db_path)

        self.session_id    = self._start_session()
        self.message_count = 0

        status = "REMOTE MEMORY SERVER" if self.online else "LOCAL DATABASE"
        self._log_to_file(
            f"SESSION STARTED | mode={mode} | "
            f"id={self.session_id} | storage={status}"
        )
        print(f"[Memory] Storage: {status}")

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _start_session(self) -> int:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO sessions (started_at, mode) VALUES (?, ?)",
            (datetime.now().isoformat(), self.mode)
        )
        sid = c.lastrowid
        conn.commit()
        conn.close()
        return sid

    def log(self, role: str, content: str):
        try:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute(
                "INSERT INTO messages (session_id, role, content, timestamp) "
                "VALUES (?, ?, ?, ?)",
                (self.session_id, role, content, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            self.message_count += 1
            preview = content[:80].replace("\n", " ")
            self._log_to_file(f"{role.upper()}: {preview}")
        except Exception as e:
            print(f"[Logger] Log error: {e}")

    def close(self):
        try:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute(
                "UPDATE sessions SET ended_at = ? WHERE id = ?",
                (datetime.now().isoformat(), self.session_id)
            )
            conn.commit()
            conn.close()
            self._log_to_file(
                f"SESSION ENDED | id={self.session_id} | "
                f"messages={self.message_count}"
            )
        except Exception as e:
            print(f"[Logger] Close error: {e}")

    def save_fact(self, key: str, value: str):
        try:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute(
                """INSERT INTO facts (key, value, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                   value=excluded.value, updated_at=excluded.updated_at""",
                (key, value, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Logger] Save fact error: {e}")

    def get_fact(self, key: str):
        try:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("SELECT value FROM facts WHERE key = ?", (key,))
            row = c.fetchone()
            conn.close()
            return row["value"] if row else None
        except Exception:
            return None

    def get_all_facts(self) -> dict:
        try:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("SELECT key, value FROM facts")
            rows = c.fetchall()
            conn.close()
            return {r["key"]: r["value"] for r in rows}
        except Exception:
            return {}

    def save_preference(self, key: str, value: str):
        try:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute(
                """INSERT INTO preferences (key, value, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                   value=excluded.value, updated_at=excluded.updated_at""",
                (key, value, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Logger] Save preference error: {e}")

    def get_preference(self, key: str):
        try:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("SELECT value FROM preferences WHERE key = ?", (key,))
            row = c.fetchone()
            conn.close()
            return row["value"] if row else None
        except Exception:
            return None

    def _log_to_file(self, text: str):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {text}\n")
        except Exception as e:
            print(f"[Logger] File log error: {e}")