import sqlite3, hashlib
from datetime import datetime

DB_PATH = "backend/exam_portal.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS exam_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exam_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS cheat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            detail TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (result_id) REFERENCES exam_results(id)
        );
    """)

    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str) -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, hash_password(password), datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return True
    
    except sqlite3.IntegrityError:
        return False # User already exist
    
def get_user_by_credentials(username: str, password: str):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    ).fetchone()
    conn.close()
    return user

def create_session(user_id: int, token: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (user_id, token, created_at) VALUES (?, ?, ?)",
        (user_id, token, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_user_by_token(token: str):
    conn = get_connection()
    user = conn.execute(
        """SELECT users.* FROM users
        JOIN sessions ON sessions.user_id = users.id
        WHERE sessions.token = ?""",
        (token,)
    ).fetchone()
    conn.close()
    return user

def save_exam_result(user_id: int, exam_id: str, score: int, total: int, started_at: str, finished_at: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO exam_results (user_id, exam_id, score, total, started_at, finished_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, exam_id, score, total, started_at, finished_at)
    )
    result_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return result_id

def save_cheat_event(result_id: int, event_type: str, detail: str=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO cheat_logs (result_id, event_type, detail, timestamp) VALUES (?, ?, ?, ?)",
        (result_id, event_type, detail, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_cheat_logs_by_result(result_id: int):
    conn = get_connection()
    logs = conn.execute(
        "SELECT * FROM cheat_logs WHERE result_id = ? ORDER BY timestamp ASC",
        (result_id,)
    ).fetchall()
    conn.close()
    return logs

def get_results_by_user(user_id: int):
    conn = get_connection()
    results = conn.execute(
        "SELECT * FROM exam_results WHERE user_id = ? ORDER BY finished_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return results