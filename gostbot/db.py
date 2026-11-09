"""Хранилище SQLite: пользователи, ответы, интервальное повторение, сессии, кэш картинок."""
import json
import sqlite3
import threading
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    name        TEXT,
    username    TEXT,
    joined      INTEGER,
    approved    INTEGER DEFAULT 0,
    daily       INTEGER DEFAULT 0,     -- присылать вопрос дня
    last_daily  TEXT                   -- дата последней рассылки (YYYY-MM-DD)
);
CREATE TABLE IF NOT EXISTS answers (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  INTEGER,
    qid      TEXT,
    correct  INTEGER,
    mode     TEXT,
    ts       INTEGER
);
CREATE INDEX IF NOT EXISTS ix_answers_user ON answers(user_id, qid);
CREATE TABLE IF NOT EXISTS review (
    user_id INTEGER,
    qid     TEXT,
    box     INTEGER,
    due     INTEGER,
    PRIMARY KEY (user_id, qid)
);
CREATE TABLE IF NOT EXISTS exams (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total   INTEGER,
    correct INTEGER,
    ts      INTEGER
);
CREATE TABLE IF NOT EXISTS sessions (
    user_id INTEGER PRIMARY KEY,
    data    TEXT
);
CREATE TABLE IF NOT EXISTS kv (
    user_id INTEGER,
    key     TEXT,
    value   TEXT,
    PRIMARY KEY (user_id, key)
);
CREATE TABLE IF NOT EXISTS reports (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  INTEGER,
    qid      TEXT,
    text     TEXT,
    ts       INTEGER,
    resolved INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS media (
    file    TEXT PRIMARY KEY,
    mtime   REAL,
    file_id TEXT
);
"""

DAY = 86400
# интервалы повторения по «коробкам» Лейтнера: 1, 3, 7, 14, 30 дней
INTERVALS = {1: 1 * DAY, 2: 3 * DAY, 3: 7 * DAY, 4: 14 * DAY, 5: 30 * DAY}
MAX_BOX = 5


class DB:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.lock:
            self.conn.executescript(SCHEMA)
            self.conn.commit()

    def _exec(self, sql, args=()):
        with self.lock:
            cur = self.conn.execute(sql, args)
            self.conn.commit()
            return cur

    def _all(self, sql, args=()):
        with self.lock:
            return self.conn.execute(sql, args).fetchall()

    def _one(self, sql, args=()):
        with self.lock:
            return self.conn.execute(sql, args).fetchone()

    # --- пользователи ---
    def touch_user(self, user_id, name, username):
        row = self._one("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        if row:
            self._exec("UPDATE users SET name=?, username=? WHERE user_id=?", (name, username, user_id))
            return False
        self._exec("INSERT INTO users(user_id, name, username, joined) VALUES (?,?,?,?)",
                   (user_id, name, username, int(time.time())))
        return True

    def get_user(self, user_id):
        return self._one("SELECT * FROM users WHERE user_id=?", (user_id,))

    def set_approved(self, user_id, value=1):
        self._exec("UPDATE users SET approved=? WHERE user_id=?", (value, user_id))

    def set_daily(self, user_id, value):
        self._exec("UPDATE users SET daily=? WHERE user_id=?", (int(value), user_id))

    def daily_users(self, today):
        return self._all("SELECT * FROM users WHERE daily=1 AND (last_daily IS NULL OR last_daily<>?)",
                         (today,))

    def mark_daily_sent(self, user_id, today):
        self._exec("UPDATE users SET last_daily=? WHERE user_id=?", (today, user_id))

    def all_users(self):
        return self._all("SELECT * FROM users ORDER BY joined")

    # --- ответы и повторение ---
    def record_answer(self, user_id, qid, correct, mode, now=None):
        now = int(now or time.time())
        self._exec("INSERT INTO answers(user_id, qid, correct, mode, ts) VALUES (?,?,?,?,?)",
                   (user_id, qid, int(correct), mode, now))
        row = self._one("SELECT box FROM review WHERE user_id=? AND qid=?", (user_id, qid))
        if not correct:
            self._exec("INSERT OR REPLACE INTO review(user_id, qid, box, due) VALUES (?,?,?,?)",
                       (user_id, qid, 1, now + INTERVALS[1]))
        elif row:
            box = row["box"] + 1
            if box > MAX_BOX:
                self._exec("DELETE FROM review WHERE user_id=? AND qid=?", (user_id, qid))
            else:
                self._exec("UPDATE review SET box=?, due=? WHERE user_id=? AND qid=?",
                           (box, now + INTERVALS[box], user_id, qid))

    def due_reviews(self, user_id, now=None):
        now = int(now or time.time())
        return [r["qid"] for r in self._all(
            "SELECT qid FROM review WHERE user_id=? AND due<=? ORDER BY due", (user_id, now))]

    def review_count(self, user_id):
        return self._one("SELECT COUNT(*) c FROM review WHERE user_id=?", (user_id,))["c"]

    def last_results(self, user_id):
        """{qid: последний ответ верный (bool)}"""
        rows = self._all("""SELECT a.qid, a.correct FROM answers a
                            JOIN (SELECT qid, MAX(id) mid FROM answers WHERE user_id=? GROUP BY qid) m
                            ON a.id=m.mid""", (user_id,))
        return {r["qid"]: bool(r["correct"]) for r in rows}

    def totals(self, user_id):
        r = self._one("SELECT COUNT(*) n, COALESCE(SUM(correct),0) c FROM answers WHERE user_id=?",
                      (user_id,))
        return r["n"], r["c"]

    def record_exam(self, user_id, total, correct):
        self._exec("INSERT INTO exams(user_id,total,correct,ts) VALUES (?,?,?,?)",
                   (user_id, total, correct, int(time.time())))

    def exam_stats(self, user_id):
        return self._one("""SELECT COUNT(*) n, MAX(CAST(correct AS REAL)/total) best
                            FROM exams WHERE user_id=?""", (user_id,))

    def reset_progress(self, user_id):
        for t in ("answers", "review", "exams", "sessions", "kv"):
            self._exec(f"DELETE FROM {t} WHERE user_id=?", (user_id,))

    # --- сессии ---
    def save_session(self, user_id, data):
        self._exec("INSERT OR REPLACE INTO sessions(user_id, data) VALUES (?,?)",
                   (user_id, json.dumps(data, ensure_ascii=False)))

    def load_session(self, user_id):
        row = self._one("SELECT data FROM sessions WHERE user_id=?", (user_id,))
        return json.loads(row["data"]) if row else None

    def drop_session(self, user_id):
        self._exec("DELETE FROM sessions WHERE user_id=?", (user_id,))

    # --- произвольные значения пользователя ---
    def set_kv(self, user_id, key, value):
        self._exec("INSERT OR REPLACE INTO kv(user_id, key, value) VALUES (?,?,?)",
                   (user_id, key, json.dumps(value, ensure_ascii=False)))

    def get_kv(self, user_id, key, default=None):
        row = self._one("SELECT value FROM kv WHERE user_id=? AND key=?", (user_id, key))
        return json.loads(row["value"]) if row else default

    # --- жалобы на вопросы ---
    def add_report(self, user_id, qid, text):
        self._exec("INSERT INTO reports(user_id, qid, text, ts) VALUES (?,?,?,?)",
                   (user_id, qid, text, int(time.time())))

    def open_reports(self, limit=30):
        return self._all("""SELECT r.*, u.name, u.username FROM reports r
                            LEFT JOIN users u ON u.user_id=r.user_id
                            WHERE resolved=0 ORDER BY r.qid, r.ts LIMIT ?""", (limit,))

    def resolve_reports(self, qid):
        return self._exec("UPDATE reports SET resolved=1 WHERE qid=? AND resolved=0", (qid,)).rowcount

    # --- кэш файлов картинок ---
    def get_media(self, file, mtime):
        row = self._one("SELECT file_id, mtime FROM media WHERE file=?", (file,))
        if row and abs(row["mtime"] - mtime) < 1e-6:
            return row["file_id"]
        return None

    def set_media(self, file, mtime, file_id):
        self._exec("INSERT OR REPLACE INTO media(file, mtime, file_id) VALUES (?,?,?)",
                   (file, mtime, file_id))

    def drop_media(self, file):
        self._exec("DELETE FROM media WHERE file=?", (file,))
