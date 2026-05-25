from bot.config import config


def meeting_url(hash: str) -> str:
    return f"{config.TERMEET_DOMAIN}/meet/{hash}"


def format_status_card(
    meeting_name: str,
    meeting_hash: str,
    participants: list[dict],
    filled_names: set[str],
    scheduled_time: str | None = None,
) -> str:
    total = len(participants)
    filled = sum(1 for p in participants if p["display_name"] in filled_names)
    lines = [
        f"📊 <b>«{meeting_name}»</b>",
        f"🔗 {meeting_url(meeting_hash)}",
        f"\n👥 Заполнили слоты: {filled}/{total}",
    ]
    for p in participants:
        mark = "✅" if p["display_name"] in filled_names else "⏳"
        lines.append(f"  {mark} {p['display_name']}")
    if scheduled_time:
        lines.append(f"\n📅 Запланировано: {scheduled_time}")
    return "\n".join(lines)


def format_all_filled_announce(
    meeting_name: str, meeting_hash: str, telemost_link: str | None = None
) -> str:
    text = (
        f"🎉 <b>Все заполнили слоты для «{meeting_name}»!</b>\n\n"
        f"🔗 Выберите финальное время: {meeting_url(meeting_hash)}"
    )
    if telemost_link:
        text += f"\n🎥 Телемост: {telemost_link}"
    return text


def format_pre_meeting_push(
    meeting_name: str, minutes: int, telemost_link: str | None = None
) -> str:
    text = f"🔔 <b>Встреча «{meeting_name}» через {minutes} минут!</b>"
    if telemost_link:
        text += f"\n🎥 Войти: {telemost_link}"
    return text
