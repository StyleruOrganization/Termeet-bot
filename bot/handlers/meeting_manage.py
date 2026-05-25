from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.context import FSMContext

from bot.api.termeet import termeet_client
from bot.database import queries as db
from bot.services.ai import parse_slots_from_text
from bot.services.notifications import meeting_url, format_status_card

router = Router()


class LinkMeeting(StatesGroup):
    waiting_hash = State()


class MySlots(StatesGroup):
    waiting_hash = State()
    waiting_text = State()


# ── /link_meeting ──────────────────────────────────────────────────────────────

@router.message(Command("link_meeting"), StateFilter(default_state))
async def cmd_link_meeting(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        await _do_link(message, args[1].strip())
    else:
        await state.set_state(LinkMeeting.waiting_hash)
        await message.answer(
            "Введите ID встречи (UUID из ссылки на termeet.tech):\n"
            "Например: <code>550e8400-e29b-41d4-a716-446655440000</code>"
        )


@router.message(LinkMeeting.waiting_hash, F.text)
async def process_link_hash(message: Message, state: FSMContext):
    await _do_link(message, message.text.strip())
    await state.clear()


async def _do_link(message: Message, hash_: str):
    try:
        meeting_data = await termeet_client.get_meeting(hash_)
    except Exception as e:
        await message.answer(f"❌ Не удалось получить встречу: {e}")
        return
    if not meeting_data:
        await message.answer("Встреча не найдена. Проверьте ID.")
        return

    chat_id = message.chat.id
    existing = await db.get_meeting(hash_)
    if existing:
        await db.link_meeting_to_chat(hash_, chat_id)
    else:
        await db.save_meeting(
            hash=hash_,
            chat_id=chat_id,
            creator_tg_id=message.from_user.id,
            name=meeting_data["name"],
        )

    await message.answer(
        f"🔗 Встреча <b>«{meeting_data['name']}»</b> привязана к этому чату.\n"
        f"{meeting_url(hash_)}"
    )


# ── /status ────────────────────────────────────────────────────────────────────

@router.message(Command("status"), StateFilter(default_state))
async def cmd_status(message: Message):
    meeting = await db.get_chat_meeting(message.chat.id)
    if not meeting:
        await message.answer(
            "В этом чате нет активной встречи.\n"
            "Создайте: /meet\nИли привяжите: /link_meeting"
        )
        return

    try:
        api_data = await termeet_client.get_meeting(meeting["hash"])
    except Exception:
        api_data = None

    participants = await db.get_participants(meeting["hash"])
    filled_names: set[str] = set()
    if api_data:
        filled_names = {
            s["name"] for s in api_data.get("slots", []) if s.get("slots")
        }

    await message.answer(
        format_status_card(
            meeting_name=meeting["name"],
            meeting_hash=meeting["hash"],
            participants=participants,
            filled_names=filled_names,
            scheduled_time=meeting.get("scheduled_time"),
        )
    )


# ── /my_slots ──────────────────────────────────────────────────────────────────

@router.message(Command("my_slots"), StateFilter(default_state))
async def cmd_my_slots(message: Message, state: FSMContext):
    if message.chat.type == "private":
        await state.set_state(MySlots.waiting_hash)
        await message.answer(
            "Введите ID встречи (UUID):\n"
            "<code>550e8400-e29b-41d4-a716-446655440000</code>"
        )
        return

    meeting = await db.get_chat_meeting(message.chat.id)
    if not meeting:
        await message.answer(
            "В этом чате нет активной встречи.\n"
            "Сначала создайте: /meet или привяжите: /link_meeting"
        )
        return

    await _ask_availability(message, state, meeting["hash"], meeting["name"])


@router.message(MySlots.waiting_hash, F.text)
async def process_my_slots_hash(message: Message, state: FSMContext):
    hash_ = message.text.strip()
    try:
        api_data = await termeet_client.get_meeting(hash_)
    except Exception:
        api_data = None
    if not api_data:
        await message.answer("Встреча не найдена. Проверьте ID и попробуйте снова.")
        return
    await state.update_data(meeting_hash=hash_, meeting_name=api_data["name"])
    await _ask_availability(message, state, hash_, api_data["name"])


async def _ask_availability(message: Message, state: FSMContext, hash_: str, name: str):
    await state.update_data(meeting_hash=hash_, meeting_name=name)
    await state.set_state(MySlots.waiting_text)

    try:
        api_data = await termeet_client.get_meeting(hash_)
        user_name = message.from_user.first_name
        current = next(
            (s for s in api_data.get("slots", []) if s["name"] == user_name), None
        )
    except Exception:
        current = None

    if current and current.get("slots"):
        slots_preview = "\n".join(
            f"  📌 {s[0]} — {s[1]}" for s in current["slots"][:5]
        )
        intro = f"Твои текущие слоты для «{name}»:\n{slots_preview}\n\n"
    else:
        intro = f"Слоты для «{name}» ещё не заполнены.\n\n"

    await message.answer(
        intro
        + "Напиши когда ты <b>свободен</b> или <b>не свободен</b> — я разберусь сам:\n"
        "<i>«Свободен в пн с 15 до 18 и в чт весь день»</i>\n"
        "<i>«Не могу в среду и в пятницу после 17:00»</i>"
    )


@router.message(MySlots.waiting_text, F.text)
async def process_my_slots_text(message: Message, state: FSMContext):
    data = await state.get_data()
    hash_ = data["meeting_hash"]
    name = data["meeting_name"]

    await state.clear()
    await message.answer("🤔 Анализирую...")

    try:
        api_data = await termeet_client.get_meeting(hash_)
        date_range = api_data.get("dataRange", [])
    except Exception:
        date_range = []

    slots = await parse_slots_from_text(message.text, date_range, name)

    if slots is None:
        await message.answer(
            "❌ Не удалось распознать время. Уточни, например:\n"
            "<i>«Свободен в понедельник с 15:00 до 18:00»</i>\n\n"
            "Или заполни вручную: " + meeting_url(hash_)
        )
        return

    user_name = message.from_user.first_name
    try:
        await termeet_client.update_slots(hash_, user_name, slots)
        await db.add_participant(hash_, user_name, message.from_user.id)
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении слотов: {e}")
        return

    if slots:
        preview = "\n".join(f"  📌 {s[0]} — {s[1]}" for s in slots)
        await message.answer(f"✅ Слоты сохранены для «{name}»!\n\n{preview}")
    else:
        await message.answer("Слоты очищены.")
