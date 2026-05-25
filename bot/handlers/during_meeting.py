import re

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram import Bot

from bot.database import queries as db
from bot.services.ai import generate_meeting_summary
from bot.services.notifications import meeting_url

router = Router()


# ── /note ──────────────────────────────────────────────────────────────────────

@router.message(Command("note"), StateFilter(default_state))
async def cmd_note(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /note текст заметки")
        return

    meeting = await db.get_chat_meeting(message.chat.id)
    if not meeting:
        await message.answer("В этом чате нет активной встречи.")
        return

    await db.save_note(meeting["hash"], message.from_user.first_name, args[1].strip())
    await message.answer("📝 Заметка сохранена.")


# ── /task ──────────────────────────────────────────────────────────────────────

@router.message(Command("task"), StateFilter(default_state))
async def cmd_task(message: Message, bot: Bot):
    """
    Usage: /task Имя Текст задачи [до ДД.ММ]
    Example: /task Иван Написать тест-кейсы до 30.05
    """
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Использование: /task Имя Текст задачи [до ДД.ММ]\n"
            "Например: <code>/task Иван Написать тест-кейсы до 30.05</code>"
        )
        return

    meeting = await db.get_chat_meeting(message.chat.id)
    if not meeting:
        await message.answer("В этом чате нет активной встречи.")
        return

    payload = args[1].strip()

    # Parse optional deadline "до DD.MM"
    deadline: str | None = None
    dl_match = re.search(r"\bдо\s+(\d{1,2}\.\d{1,2}(?:\.\d{2,4})?)\s*$", payload, re.I)
    if dl_match:
        deadline = dl_match.group(1)
        payload = payload[: dl_match.start()].strip()

    # First token = assignee name
    parts = payload.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Укажи имя исполнителя и текст задачи.")
        return

    assignee_name = parts[0].lstrip("@")
    task_text = parts[1]

    # Try to find assignee's tg_id from participants
    participants = await db.get_participants(meeting["hash"])
    assignee_tg_id: int | None = None
    for p in participants:
        if p["display_name"].lower() == assignee_name.lower():
            assignee_tg_id = p.get("tg_user_id")
            break

    await db.save_task(
        meeting_hash=meeting["hash"],
        assignee_name=assignee_name,
        text=task_text,
        deadline=deadline,
        assignee_tg_id=assignee_tg_id,
    )

    dl_str = f" (до {deadline})" if deadline else ""
    await message.answer(
        f"✅ Задача зафиксирована:\n"
        f"<b>{assignee_name}</b>: {task_text}{dl_str}"
    )

    # DM the assignee if we know their Telegram ID
    if assignee_tg_id:
        try:
            await bot.send_message(
                assignee_tg_id,
                f"📌 На встрече «{meeting['name']}» тебе назначена задача:\n"
                f"<b>{task_text}</b>{dl_str}",
            )
        except Exception:
            pass


# ── /end_meeting ───────────────────────────────────────────────────────────────

@router.message(Command("end_meeting"), StateFilter(default_state))
async def cmd_end_meeting(message: Message):
    meeting = await db.get_chat_meeting(message.chat.id)
    if not meeting:
        await message.answer("В этом чате нет активной встречи.")
        return

    if meeting["creator_tg_id"] != message.from_user.id:
        await message.answer("Завершить встречу может только организатор.")
        return

    hash_ = meeting["hash"]
    notes = await db.get_notes(hash_)
    tasks = await db.get_tasks(hash_)

    await db.update_meeting_status(hash_, "ended")
    await message.answer("🏁 Встреча завершена! Генерирую итоги...")

    summary = await generate_meeting_summary(meeting["name"], notes, tasks)

    tasks_block = ""
    if tasks:
        tasks_block = "\n\n✅ <b>Задачи:</b>\n"
        for t in tasks:
            dl = f" (до {t['deadline']})" if t["deadline"] else ""
            icon = "✔️" if t["status"] == "done" else "⏳"
            tasks_block += f"  {icon} <b>{t['assignee_name']}</b>: {t['text']}{dl}\n"

    await message.answer(
        f"📋 <b>Итоги встречи «{meeting['name']}»</b>\n\n"
        f"{summary}"
        f"{tasks_block}"
    )
