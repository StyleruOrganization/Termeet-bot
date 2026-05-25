from datetime import datetime

from aiogram import Bot

from bot.api.termeet import termeet_client
from bot.database import queries as db
from bot.services.notifications import meeting_url, format_all_filled_announce, format_pre_meeting_push


async def check_and_nag(bot: Bot):
    """
    Every 4 hours: fetch each planning meeting, check who hasn't filled slots.
    - If all filled → announce and mark scheduled.
    - If not all → nag in group chat + DM those with known tg_id.
    """
    meetings = await db.get_all_active_meetings()
    for meeting in meetings:
        hash_ = meeting["hash"]
        try:
            api_data = await termeet_client.get_meeting(hash_)
        except Exception:
            continue
        if not api_data:
            continue

        filled_names = {
            s["name"] for s in api_data.get("slots", []) if s.get("slots")
        }
        participants = await db.get_participants(hash_)
        if not participants:
            continue

        unfilled = [p for p in participants if p["display_name"] not in filled_names]

        chat_id = meeting.get("chat_id")

        if not unfilled:
            await db.update_meeting_status(hash_, "scheduled")
            if chat_id:
                await bot.send_message(
                    chat_id,
                    format_all_filled_announce(
                        meeting["name"], hash_, meeting.get("telemost_link")
                    ),
                )
            continue

        # Nag in group chat
        if chat_id:
            names_str = ", ".join(
                f"<b>{p['display_name']}</b>" for p in unfilled
            )
            await bot.send_message(
                chat_id,
                f"⏳ Ждём слоты для «{meeting['name']}»\n"
                f"Ещё не заполнили: {names_str}\n"
                f"Заполнить: {meeting_url(hash_)} или /my_slots",
            )

        # DM participants with known tg_id
        for p in unfilled:
            tg_id = p.get("tg_user_id")
            if tg_id:
                try:
                    await bot.send_message(
                        tg_id,
                        f"👋 Заполни слоты для встречи «{meeting['name']}»:\n"
                        f"{meeting_url(hash_)}\n\n"
                        "Или напиши мне /my_slots прямо здесь.",
                    )
                except Exception:
                    pass


async def send_pre_meeting_reminders(bot: Bot):
    """
    Every 5 minutes: send reminders ~1 hour and ~10 minutes before scheduled meetings.
    """
    meetings = await db.get_all_scheduled_meetings()
    now = datetime.now()

    for meeting in meetings:
        scheduled_raw = meeting.get("scheduled_time")
        chat_id = meeting.get("chat_id")
        if not scheduled_raw or not chat_id:
            continue
        try:
            meeting_time = datetime.fromisoformat(scheduled_raw)
        except ValueError:
            continue

        diff_minutes = (meeting_time - now).total_seconds() / 60

        if 55 <= diff_minutes <= 65:
            await bot.send_message(
                chat_id,
                format_pre_meeting_push(meeting["name"], 60, meeting.get("telemost_link")),
            )
        elif 8 <= diff_minutes <= 12:
            await bot.send_message(
                chat_id,
                format_pre_meeting_push(meeting["name"], 10, meeting.get("telemost_link")),
            )


async def send_task_follow_ups(bot: Bot):
    """
    Daily: ping task assignees whose deadlines are tomorrow or overdue.
    """
    meetings = await db.get_all_scheduled_meetings()
    today = datetime.now().date()

    for meeting in meetings:
        if meeting["status"] not in ("scheduled", "ended"):
            continue
        tasks = await db.get_tasks(meeting["hash"])
        for task in tasks:
            if task["status"] == "done" or not task.get("deadline"):
                continue
            tg_id = task.get("assignee_tg_id")
            if not tg_id:
                continue
            try:
                deadline = datetime.strptime(task["deadline"], "%d.%m").date().replace(
                    year=today.year
                )
            except ValueError:
                continue

            days_left = (deadline - today).days
            if days_left in (1, 0, -1):
                status_word = (
                    "завтра" if days_left == 1
                    else "сегодня" if days_left == 0
                    else "вчера (просрочено)"
                )
                try:
                    await bot.send_message(
                        tg_id,
                        f"⚠️ Напоминание о задаче из «{meeting['name']}»:\n"
                        f"<b>{task['text']}</b>\n"
                        f"Дедлайн: {status_word} ({task['deadline']})\n\n"
                        "Если сделал — отлично! Если нет — не забудь.",
                    )
                except Exception:
                    pass
