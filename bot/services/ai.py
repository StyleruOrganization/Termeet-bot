import json
from datetime import date
from bot.config import config


async def parse_slots_from_text(
    user_text: str, meeting_date_range: list, meeting_name: str
) -> list | None:
    """Parse natural language availability into API slot pairs via Claude."""
    if not config.CLAUDE_API_KEY:
        return None
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=config.CLAUDE_API_KEY)
        today = date.today().isoformat()
        system = (
            f'You are a time-slot parser for meeting scheduler "{meeting_name}".\n'
            f"Meeting date range: {meeting_date_range}. Today: {today}.\n"
            "Convert the user's availability description into JSON.\n"
            "Return ONLY a JSON array of [start, end] pairs in ISO-8601 format "
            '(YYYY-MM-DDTHH:MM:SS). Example: [["2026-05-27T15:00:00","2026-05-27T18:00:00"]].\n'
            "If nothing can be parsed, return []."
        )
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": user_text}],
        )
        raw = msg.content[0].text.strip()
        slots = json.loads(raw)
        return slots if isinstance(slots, list) else None
    except Exception:
        return None


async def generate_meeting_summary(
    meeting_name: str, notes: list[dict], tasks: list[dict]
) -> str:
    """Generate AI summary after meeting ends. Falls back to plain format."""
    if config.CLAUDE_API_KEY:
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=config.CLAUDE_API_KEY)
            notes_txt = "\n".join(
                f"- {n['author_name']}: {n['text']}" for n in notes
            ) or "нет заметок"
            tasks_txt = "\n".join(
                f"- {t['assignee_name']}: {t['text']}"
                + (f" (до {t['deadline']})" if t["deadline"] else "")
                for t in tasks
            ) or "нет задач"
            prompt = (
                f'Составь краткое резюме встречи "{meeting_name}" на русском.\n\n'
                f"Заметки:\n{notes_txt}\n\nЗадачи:\n{tasks_txt}\n\n"
                "Формат:\n📝 Резюме: [2-3 предложения]\n"
                "✅ Решения: [список]\n⚠️ Открытые вопросы: [если есть]"
            )
            msg = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception:
            pass
    return _plain_summary(meeting_name, notes, tasks)


def _plain_summary(meeting_name: str, notes: list[dict], tasks: list[dict]) -> str:
    lines = [f"📋 <b>Итоги «{meeting_name}»</b>"]
    if notes:
        lines.append("\n📝 <b>Заметки:</b>")
        for n in notes:
            lines.append(f"• {n['author_name']}: {n['text']}")
    if tasks:
        lines.append("\n✅ <b>Задачи:</b>")
        for t in tasks:
            dl = f" (до {t['deadline']})" if t["deadline"] else ""
            lines.append(f"• {t['assignee_name']}: {t['text']}{dl}")
    return "\n".join(lines)
