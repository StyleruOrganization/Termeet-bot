import aiosqlite
from bot.database.db import DB_PATH


async def save_meeting(hash: str, chat_id: int | None, creator_tg_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO meetings (hash, chat_id, creator_tg_id, name) VALUES (?, ?, ?, ?)",
            (hash, chat_id, creator_tg_id, name),
        )
        await db.commit()


async def get_meeting(hash: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM meetings WHERE hash = ?", (hash,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_chat_meeting(chat_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM meetings WHERE chat_id = ? AND status != 'ended' ORDER BY created_at DESC LIMIT 1",
            (chat_id,),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def update_meeting_status(hash: str, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE meetings SET status = ? WHERE hash = ?", (status, hash))
        await db.commit()


async def update_meeting_scheduled_time(hash: str, scheduled_time: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE meetings SET scheduled_time = ?, status = 'scheduled' WHERE hash = ?",
            (scheduled_time, hash),
        )
        await db.commit()


async def update_meeting_telemost(hash: str, telemost_link: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE meetings SET telemost_link = ? WHERE hash = ?", (telemost_link, hash)
        )
        await db.commit()


async def link_meeting_to_chat(hash: str, chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE meetings SET chat_id = ? WHERE hash = ?", (chat_id, hash)
        )
        await db.commit()


async def add_participant(meeting_hash: str, display_name: str, tg_user_id: int | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO participants (meeting_hash, display_name, tg_user_id) VALUES (?, ?, ?)",
            (meeting_hash, display_name, tg_user_id),
        )
        await db.commit()


async def get_participants(meeting_hash: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM participants WHERE meeting_hash = ?", (meeting_hash,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def save_note(meeting_hash: str, author_name: str, text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO notes (meeting_hash, author_name, text) VALUES (?, ?, ?)",
            (meeting_hash, author_name, text),
        )
        await db.commit()


async def get_notes(meeting_hash: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM notes WHERE meeting_hash = ? ORDER BY created_at", (meeting_hash,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def save_task(
    meeting_hash: str,
    assignee_name: str,
    text: str,
    deadline: str | None = None,
    assignee_tg_id: int | None = None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO tasks (meeting_hash, assignee_name, assignee_tg_id, text, deadline) VALUES (?, ?, ?, ?, ?)",
            (meeting_hash, assignee_name, assignee_tg_id, text, deadline),
        )
        await db.commit()
        return cur.lastrowid


async def get_tasks(meeting_hash: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tasks WHERE meeting_hash = ? ORDER BY created_at", (meeting_hash,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def complete_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,))
        await db.commit()


async def get_all_active_meetings() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM meetings WHERE status = 'planning' AND chat_id IS NOT NULL"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_all_scheduled_meetings() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM meetings WHERE status = 'scheduled' AND scheduled_time IS NOT NULL"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def upsert_chat_member(
    chat_id: int,
    tg_user_id: int,
    first_name: str,
    username: str | None = None,
    last_name: str | None = None,
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO chat_members (chat_id, tg_user_id, username, first_name, last_name, last_seen)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(chat_id, tg_user_id) DO UPDATE SET
                   username=excluded.username,
                   first_name=excluded.first_name,
                   last_name=excluded.last_name,
                   last_seen=CURRENT_TIMESTAMP""",
            (chat_id, tg_user_id, username, first_name, last_name),
        )
        await db.commit()


async def get_chat_members(chat_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM chat_members WHERE chat_id = ? ORDER BY first_name",
            (chat_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_ended_meetings_before(dt_iso: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM meetings WHERE status = 'ended' AND created_at <= ?", (dt_iso,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
