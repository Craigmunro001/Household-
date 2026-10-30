import json
import sqlite3
import time
from dataclasses import asdict
from pathlib import Path

from .flow import Session


class SessionStore:
    def __init__(self, path):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS sessions (phone TEXT PRIMARY KEY, data TEXT NOT NULL, updated REAL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS seen (msg_id TEXT PRIMARY KEY, ts REAL)")
        self.db.commit()

    def load(self, phone):
        row = self.db.execute("SELECT data FROM sessions WHERE phone=?", (phone,)).fetchone()
        return Session(**json.loads(row[0])) if row else Session(phone=phone)

    def save(self, s):
        self.db.execute(
            "INSERT INTO sessions(phone, data, updated) VALUES(?,?,?) "
            "ON CONFLICT(phone) DO UPDATE SET data=excluded.data, updated=excluded.updated",
            (s.phone, json.dumps(asdict(s)), time.time()),
        )
        self.db.commit()

    def first_time_seen(self, msg_id):
        """WhatsApp retries webhooks; return False if we've already handled this message id."""
        try:
            self.db.execute("INSERT INTO seen(msg_id, ts) VALUES(?,?)", (msg_id, time.time()))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False
