import json
import sys
from datetime import date
from bot.config import config


class AINotAvailableError(Exception):
    """Raised when CLAUDE_API_KEY is not configured."""


def _dates_from_range(data_range: list) -> list[str]:
    """Extract sorted unique date strings from API dataRange."""
    seen: set[str] = set()
    result: list[str] = []
    for pair in data_range:
        if pair and pair[0]:
            d = pair[0][:10]  # "2026-05-27" from "2026-05-27T06:00:00Z"
            if d not in seen:
                seen.add(d)
                result.append(d)
    return sorted(result)


async def parse_slots_from_text(
    user_text: str, meeting_date_range: list, meeting_name: str
) -> list:
    """
    Parse natural language availability into slot pairs via Claude.

    Returns list of [start, end] pairs (may be empty if Claude can't parse).
    Raises AINotAvailableError if CLAUDE_API_KEY is not set.
    """
    if not config.claude.API_KEY:
        raise AINotAvailableError("CLAUDE_API_KEY not configured")

    import anthropic

    client = anthropic.AsyncAnthropic(api_key=config.claude.API_KEY)
    today = date.today().isoformat()

    # Give Claude simple date strings instead of raw UTC datetime pairs
    meeting_dates = _dates_from_range(meeting_date_range)
    dates_str = ", ".join(meeting_dates) if meeting_dates else "unknown"

    # Build a few example lines based on real dates so Claude knows what to output
    if meeting_dates:
        ex_d = meeting_dates[0]
        example_out = f'[["{ex_d}T19:00:00","{ex_d}T20:00:00"]]'
        if len(meeting_dates) > 1:
            ex_d2 = meeting_dates[1]
            example_out = (
                f'[["{ex_d}T19:00:00","{ex_d}T20:00:00"],'
                f'["{ex_d2}T19:00:00","{ex_d2}T20:00:00"]]'
            )
    else:
        example_out = '[["2026-05-27T19:00:00","2026-05-27T20:00:00"]]'

    system = f"""You are a time-slot parser for a Russian Telegram meeting bot.
Meeting: "{meeting_name}"
Dates available for this meeting: {dates_str}
Today: {today}

The user describes in Russian when they are FREE or BUSY.
Your job: return a JSON array of available [start, end] datetime pairs for the LISTED DATES ONLY.

Rules:
- Return ONLY a raw JSON array, no explanation, no markdown
- Format: YYYY-MM-DDTHH:MM:SS (no timezone suffix)
- "каждый день" / "ежедневно" = one slot per EVERY date listed above
- "понедельник"/"пн" = find the Monday(s) in the listed dates
- "вторник"/"вт" = Tuesday(s), etc.
- "с X до Y" = from X:00:00 to Y:00:00 (treat as local time)
- "весь день" = 09:00:00 to 21:00:00
- If user says BUSY/CAN'T (не смогу, занят, не могу) → exclude those days/times
- If unparseable or nothing available → return []

Example — dates="{dates_str}", user says "свободен с 19 до 20 каждый день":
{example_out}"""

    try:
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user_text}],
        )
        raw = msg.content[0].text.strip()
        # Strip markdown code blocks if Claude wrapped it
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        slots = json.loads(raw)
        return slots if isinstance(slots, list) else []
    except Exception as e:
        print(f"[ai.parse_slots] error: {e!r}", file=sys.stderr, flush=True)
        return []


async def generate_meeting_summary(
    meeting_name: str, notes: list[dict], tasks: list[dict]
) -> str:
    """Generate AI summary after meeting ends. Falls back to plain format."""
    if config.claude.API_KEY:
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=config.claude.API_KEY)
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
