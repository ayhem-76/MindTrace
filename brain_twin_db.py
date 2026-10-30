
import hashlib
import json
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


# Keep the database in the MindTrace project folder.
DB_PATH = Path(__file__).resolve().parent / "mindtrace.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_db():
    with get_connection() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS assessment_runs (
                run_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                cognitive_index INTEGER NOT NULL,
                correct_count INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                average_seconds REAL NOT NULL,
                category_scores_json TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_runs_user_date
            ON assessment_runs(user_id, completed_at);
        """)


def hash_password(password, salt_hex=None):
    if salt_hex is None:
        salt_hex = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        300_000,
    ).hex()

    return salt_hex, password_hash


def create_user(username, password):
    username = username.strip()

    if len(username) < 3:
        raise ValueError("Username must contain at least 3 characters.")

    if len(password) < 10:
        raise ValueError("Password must contain at least 10 characters.")

    salt, password_hash = hash_password(password)
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO users
                (user_id, username, password_salt,
                 password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, username, salt, password_hash, created_at),
        )

    return user_id


def authenticate_user(username, password):
    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT user_id, password_salt, password_hash
            FROM users
            WHERE username = ? COLLATE NOCASE
            """,
            (username.strip(),),
        ).fetchone()

    if user is None:
        return None

    _, candidate_hash = hash_password(password, user["password_salt"])

    if secrets.compare_digest(candidate_hash, user["password_hash"]):
        return user["user_id"]

    return None


def save_assessment(
    user_id,
    cognitive_index,
    correct_count,
    total_questions,
    average_seconds,
    category_scores,
):
    run_id = str(uuid.uuid4())
    completed_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO assessment_runs (
                run_id, user_id, completed_at, cognitive_index,
                correct_count, total_questions, average_seconds,
                category_scores_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                user_id,
                completed_at,
                int(cognitive_index),
                int(correct_count),
                int(total_questions),
                float(average_seconds),
                json.dumps(category_scores),
            ),
        )

    return run_id


def get_user_history(user_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT run_id, completed_at, cognitive_index,
                   correct_count, total_questions, average_seconds,
                   category_scores_json
            FROM assessment_runs
            WHERE user_id = ?
            ORDER BY completed_at ASC
            """,
            (user_id,),
        ).fetchall()

    history = []

    for row in rows:
        item = dict(row)
        item["category_scores"] = json.loads(
            item.pop("category_scores_json")
        )
        history.append(item)

    return history


def delete_user(user_id):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM users WHERE user_id = ?",
            (user_id,),
        )


initialize_db()
