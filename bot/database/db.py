import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "termeet.db"

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS meetings (
    hash TEXT PRIMARY KEY,
    chat_id INTEGER,
    creator_tg_id INTEGER,
    name TEXT NOT NULL,
    telemost_link TEXT,
    scheduled_time TEXT,
    status TEXT DEFAULT 'planning',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_hash TEXT NOT NULL,
    tg_user_id INTEGER,
    display_name TEXT NOT NULL,
    UNIQUE(meeting_hash, display_name)
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_hash TEXT NOT NULL,
    author_name TEXT,
    text TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_hash TEXT NOT NULL,
    assignee_tg_id INTEGER,
    assignee_name TEXT NOT NULL,
    text TEXT NOT NULL,
    deadline TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_members (
    chat_id INTEGER NOT NULL,
    tg_user_id INTEGER NOT NULL,
    username TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, tg_user_id)
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()
