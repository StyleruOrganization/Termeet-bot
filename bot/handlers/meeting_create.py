import re
from datetime import date, timedelta

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.context import FSMContext

from bot.api.termeet import termeet_client
from bot.database import queries as db
from bot.services.notifications import meeting_url

router = Router()

# Preset working-hours windows shown as buttons
_TIME_PRESETS: dict[str, tuple[str, str]] = {
    "tw_0918": ("09:00", "18:00"),
    "tw_0919": ("09:00", "19:00"),
    "tw_1018": ("10:00", "18:00"),
    "tw_1020": ("10:00", "20:00"),
}

# UTC offset presets: callback_data → (offset_hours, label)
_TZ_PRESETS: dict[str, tuple[int, str]] = {
    "tz_p2": (2, "UTC+2  Калининград"),
    "tz_p3": (3, "UTC+3  Москва"),
    "tz_p4": (4, "UTC+4  Самара"),
    "tz_p5": (5, "UTC+5  Екатеринбург"),
    "tz_p6": (6, "UTC+6  Омск"),
    "tz_p7": (7, "UTC+7  Красноярск"),
    "tz_p8": (8, "UTC+8  Иркутск"),
    "tz_p9": (9, "UTC+9  Якутск"),
    "tz_p10": (10, "UTC+10 Владивосток"),
    "tz_p11": (11, "UTC+11 Магадан"),
    "tz_p12": (12, "UTC+12 Камчатка"),
}


class MeetCreate(StatesGroup):
    name = State()
    date_from = State()
    date_to = State()
    time_window = State()  # рабочие часы (локальное время)
    timezone = State()  # UTC-смещение
    duration = State()
    description = State()
    # participants_mode = State()  # выбор: из чата / вручную / пропустить
    # participants_select = State()  # выбор из известных участников чата
    # participants = State()  # ручной ввод имён


def _parse_date(text: str) -> date | None:
    text = text.strip()
    today = date.today()
    patterns = [
        r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$",
        r"^(\d{1,2})\.(\d{1,2})\.(\d{2})$",
        r"^(\d{1,2})\.(\d{1,2})$",
    ]
    for pat in patterns:
        m = re.match(pat, text)
        if m:
            groups = m.groups()
            day, month = int(groups[0]), int(groups[1])
            year = today.year
            if len(groups) == 3:
                y = int(groups[2])
                year = 2000 + y if y < 100 else y
            try:
                d = date(year, month, day)
                if d < today:
                    d = date(year + 1, month, day)
                return d
            except ValueError:
                return None
    return None


def _build_data_range(
    date_from: str,
    date_to: str,
    time_from: str,
    time_to: str,
    utc_offset: int,
) -> list[list[str]]:
    """
    One UTC time-window per day in [date_from, date_to].

    Converts local time_from/time_to to UTC for every day.
    If time_to <= time_from locally (window crosses midnight), end is next local day.

    Example: 22:00-02:00 local UTC+0, Dec 21-23:
      [["2026-12-21T22:00:00Z","2026-12-22T02:00:00Z"],
       ["2026-12-22T22:00:00Z","2026-12-23T02:00:00Z"],
       ["2026-12-23T22:00:00Z","2026-12-24T02:00:00Z"]]
    """
    start_date = date.fromisoformat(date_from)
    end_date = date.fromisoformat(date_to)
    tf_h, tf_m = map(int, time_from.split(":"))
    tt_h, tt_m = map(int, time_to.split(":"))
    # Window crosses local midnight when end <= start
    end_day_shift = 1 if (tt_h, tt_m) <= (tf_h, tf_m) else 0

    result: list[list[str]] = []
    current = start_date
    while current <= end_date:
        # Start: local time_from on 'current' → UTC
        s_h = tf_h - utc_offset
        s_day = current
        if s_h < 0:
            s_h += 24
            s_day = current - timedelta(days=1)
        elif s_h >= 24:
            s_h -= 24
            s_day = current + timedelta(days=1)

        # End: local time_to on (current + end_day_shift) → UTC
        e_base = current + timedelta(days=end_day_shift)
        e_h = tt_h - utc_offset
        e_day = e_base
        if e_h < 0:
            e_h += 24
            e_day = e_base - timedelta(days=1)
        elif e_h >= 24:
            e_h -= 24
            e_day = e_base + timedelta(days=1)

        result.append(
            [
                f"{s_day.isoformat()}T{s_h:02d}:{tf_m:02d}:00Z",
                f"{e_day.isoformat()}T{e_h:02d}:{tt_m:02d}:00Z",
            ]
        )
        current += timedelta(days=1)
    return result


def _time_window_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="09:00 – 18:00", callback_data="tw_0918"
                ),
                InlineKeyboardButton(
                    text="09:00 – 19:00", callback_data="tw_0919"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="10:00 – 18:00", callback_data="tw_1018"
                ),
                InlineKeyboardButton(
                    text="10:00 – 20:00", callback_data="tw_1020"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Своё время", callback_data="tw_custom"
                ),
            ],
        ]
    )


def _timezone_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="UTC+2 Калининград", callback_data="tz_p2"
                ),
                InlineKeyboardButton(
                    text="UTC+3 Москва", callback_data="tz_p3"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="UTC+4 Самара", callback_data="tz_p4"
                ),
                InlineKeyboardButton(
                    text="UTC+5 Екатеринбург", callback_data="tz_p5"
                ),
            ],
            [
                InlineKeyboardButton(text="UTC+6 Омск", callback_data="tz_p6"),
                InlineKeyboardButton(
                    text="UTC+7 Красноярск", callback_data="tz_p7"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="UTC+8 Иркутск", callback_data="tz_p8"
                ),
                InlineKeyboardButton(
                    text="UTC+9 Якутск", callback_data="tz_p9"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="UTC+10 Владивосток", callback_data="tz_p10"
                ),
                InlineKeyboardButton(
                    text="UTC+11 Магадан", callback_data="tz_p11"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="UTC+12 Камчатка", callback_data="tz_p12"
                ),
                InlineKeyboardButton(
                    text="✏️ Другой UTC+N", callback_data="tz_custom"
                ),
            ],
        ]
    )


def _duration_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="30 мин", callback_data="dur_30"),
                InlineKeyboardButton(text="1 час", callback_data="dur_60"),
            ],
            [
                InlineKeyboardButton(text="1.5 часа", callback_data="dur_90"),
                InlineKeyboardButton(text="2 часа", callback_data="dur_120"),
            ],
        ]
    )


# Создание встречи
@router.message(Command("meet"), StateFilter(default_state))
async def cmd_meet(message: Message, state: FSMContext):
    await state.set_state(MeetCreate.name)
    await message.answer("📅 <b>Создание встречи</b>\n\nКак назовём встречу?")


# Выбор даты
@router.message(MeetCreate.name, F.text)
async def step_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(MeetCreate.date_from)
    await message.answer(
        "📆 С какой даты ищем время?\n"
        "Введите в формате <b>ДД.ММ</b>, например: <code>27.05</code>"
    )


@router.message(MeetCreate.date_from, F.text)
async def step_date_from(message: Message, state: FSMContext):
    d = _parse_date(message.text)
    if not d:
        await message.answer(
            "Не удалось распознать дату. Попробуйте формат ДД.ММ, например: 27.05"
        )
        return
    await state.update_data(date_from=d.isoformat())
    await state.set_state(MeetCreate.date_to)
    await message.answer("📆 По какую дату? (тот же формат <b>ДД.ММ</b>)")


@router.message(MeetCreate.date_to, F.text)
async def step_date_to(message: Message, state: FSMContext):
    d = _parse_date(message.text)
    if not d:
        await message.answer(
            "Не удалось распознать дату. Попробуйте формат ДД.ММ, например: 31.05"
        )
        return
    data = await state.get_data()
    if d.isoformat() < data["date_from"]:
        await message.answer(
            "Конечная дата должна быть не раньше начальной. Попробуйте ещё раз."
        )
        return
    await state.update_data(date_to=d.isoformat())
    await state.set_state(MeetCreate.time_window)
    await message.answer(
        "🕐 В какие часы ищем время?\n"
        "Выберите рабочий диапазон, который будет применён ко всем дням:",
        reply_markup=_time_window_kb(),
    )


# Выбор часового пояса
@router.callback_query(MeetCreate.time_window, F.data.in_(_TIME_PRESETS))
async def step_time_window_preset(callback: CallbackQuery, state: FSMContext):
    t_from, t_to = _TIME_PRESETS[callback.data]
    await state.update_data(time_from=t_from, time_to=t_to)
    await state.set_state(MeetCreate.timezone)
    await callback.message.edit_text(
        f"✅ Часы: {t_from} – {t_to}\n\n🌍 Выберите ваш часовой пояс:",
        reply_markup=_timezone_kb(),
    )
    await callback.answer()


@router.callback_query(MeetCreate.time_window, F.data == "tw_custom")
async def step_time_window_custom_prompt(callback: CallbackQuery):
    await callback.message.edit_text(
        "Введите диапазон в формате <b>ЧЧ:ММ–ЧЧ:ММ</b>\n"
        "Например: <code>08:00–20:00</code>"
    )
    await callback.answer()


@router.message(MeetCreate.time_window, F.text)
async def step_time_window_custom(message: Message, state: FSMContext):
    m = re.match(
        r"^(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})$", message.text.strip()
    )
    if not m:
        await message.answer(
            "Не распознал формат. Попробуйте: <code>09:00–18:00</code>",
            reply_markup=_time_window_kb(),
        )
        return
    t_from, t_to = m.group(1), m.group(2)
    await state.update_data(time_from=t_from, time_to=t_to)
    await state.set_state(MeetCreate.timezone)
    await message.answer(
        f"✅ Часы: {t_from} – {t_to}\n\n🌍 Выберите ваш часовой пояс:",
        reply_markup=_timezone_kb(),
    )


# Выбор часового пояса
@router.callback_query(MeetCreate.timezone, F.data.in_(_TZ_PRESETS))
async def step_timezone_preset(callback: CallbackQuery, state: FSMContext):
    offset, label = _TZ_PRESETS[callback.data]
    await state.update_data(utc_offset=offset, tz_label=label)
    await state.set_state(MeetCreate.duration)
    await callback.message.edit_text(
        f"✅ Часовой пояс: {label}\n\n⏱ Сколько длится встреча?",
        reply_markup=_duration_kb(),
    )
    await callback.answer()


@router.callback_query(MeetCreate.timezone, F.data == "tz_custom")
async def step_timezone_custom_prompt(callback: CallbackQuery):
    await callback.message.edit_text(
        "Введите UTC-смещение числом.\n"
        "Например: <code>3</code> для UTC+3, <code>-5</code> для UTC-5"
    )
    await callback.answer()


@router.message(MeetCreate.timezone, F.text)
async def step_timezone_custom(message: Message, state: FSMContext):
    try:
        offset = int(message.text.strip().replace("+", ""))
        if not (-12 <= offset <= 14):
            raise ValueError
    except ValueError:
        await message.answer(
            "Некорректное смещение. Введите число от -12 до 14, например: <code>3</code>",
            reply_markup=_timezone_kb(),
        )
        return
    label = f"UTC{offset:+d}"
    await state.update_data(utc_offset=offset, tz_label=label)
    await state.set_state(MeetCreate.duration)
    await message.answer(
        f"✅ Часовой пояс: {label}\n\n⏱ Сколько длится встреча?",
        reply_markup=_duration_kb(),
    )


# Добавление описания встречи
@router.callback_query(MeetCreate.duration, F.data.startswith("dur_"))
async def step_duration(callback: CallbackQuery, state: FSMContext):
    minutes = callback.data.split("_")[1]
    labels = {"30": "30 мин", "60": "1 час", "90": "1.5 часа", "120": "2 часа"}
    await state.update_data(duration=labels.get(minutes, f"{minutes} мин"))
    await state.set_state(MeetCreate.description)
    await callback.message.edit_text(
        "📝 Добавьте описание встречи (необязательно).\n" "Или отправьте /skip"
    )
    await callback.answer()


@router.message(MeetCreate.description, F.text)
async def step_description(message: Message, state: FSMContext):
    if message.text.strip() != "/skip":
        await state.update_data(description=message.text.strip())
    await state.set_state(MeetCreate.participants_mode)
    await _finish_creation(
        message,
        state,
        [],
        message.from_user.id,
        message.from_user.first_name,
    )


# ── participants_mode ──────────────────────────────────────────────────────────


# def _participants_mode_kb(chat_type: str) -> InlineKeyboardMarkup:
#     rows = []
#     if chat_type in ("group", "supergroup"):
#         rows.append(
#             [
#                 InlineKeyboardButton(
#                     text="👥 Из участников чата",
#                     callback_data="pm_auto",
#                 )
#             ]
#         )
#     rows.append(
#         [
#             InlineKeyboardButton(
#                 text="✍️ Ввести вручную", callback_data="pm_manual"
#             )
#         ]
#     )
#     rows.append(
#         [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="pm_skip")]
#     )
#     return InlineKeyboardMarkup(inline_keyboard=rows)


# def _members_select_kb(
#     members: list[dict], selected_ids: list[int]
# ) -> InlineKeyboardMarkup:
#     sel = set(selected_ids)
#     rows = []
#     for m in members:
#         uid = m["tg_user_id"]
#         name = m["first_name"]
#         if m.get("last_name"):
#             name += f" {m['last_name']}"
#         icon = "✅" if uid in sel else "☐"
#         rows.append(
#             [
#                 InlineKeyboardButton(
#                     text=f"{icon} {name}",
#                     callback_data=f"msel_{uid}",
#                 )
#             ]
#         )
#     rows.append(
#         [
#             InlineKeyboardButton(
#                 text=f"✅ Готово ({len(sel)} выбрано)",
#                 callback_data="msel_done",
#             )
#         ]
#     )
#     rows.append(
#         [
#             InlineKeyboardButton(
#                 text="✍️ Добавить вручную",
#                 callback_data="msel_add_manual",
#             )
#         ]
#     )
#     return InlineKeyboardMarkup(inline_keyboard=rows)


# @router.callback_query(MeetCreate.participants_mode, F.data == "pm_auto")
# async def step_pm_auto(callback: CallbackQuery, state: FSMContext):
#     chat_id = callback.message.chat.id
#     members = await db.get_chat_members(chat_id)
#     if not members:
#         await callback.answer(
#             "Пока нет данных об участниках чата — бот запоминает всех, "
#             "кто пишет сообщения. Попробуйте позже или введите имена вручную.",
#             show_alert=True,
#         )
#         return

#     # Pre-select everyone
#     selected_ids = [m["tg_user_id"] for m in members]
#     await state.update_data(members_list=members, selected_ids=selected_ids)
#     await state.set_state(MeetCreate.participants_select)
#     await callback.message.edit_text(
#         "👥 Выберите участников встречи\n"
#         "(все выбраны по умолчанию — снимите галочку, чтобы исключить):",
#         reply_markup=_members_select_kb(members, selected_ids),
#     )
#     await callback.answer()


# @router.callback_query(MeetCreate.participants_mode, F.data == "pm_manual")
# async def step_pm_manual(callback: CallbackQuery, state: FSMContext):
#     await state.set_state(MeetCreate.participants)
#     await callback.message.edit_text(
#         "✍️ Перечислите участников через запятую.\n"
#         "Используйте имена, которыми они представятся на сайте.\n"
#         "Например: <i>Иван, Маша, Петя</i>"
#     )
#     await callback.answer()


# @router.callback_query(MeetCreate.participants_mode, F.data == "pm_skip")
# async def step_pm_skip(callback: CallbackQuery, state: FSMContext):
#     await callback.answer()
#     await _finish_creation(
#         callback.message,
#         state,
#         [],
#         callback.from_user.id,
#         callback.from_user.first_name,
#     )


# # ── participants_select (toggle checkboxes) ────────────────────────────────────


# @router.callback_query(
#     MeetCreate.participants_select, F.data.startswith("msel_")
# )
# async def step_members_toggle(callback: CallbackQuery, state: FSMContext):
#     data = await state.get_data()
#     members: list[dict] = data["members_list"]
#     selected_ids: list[int] = data["selected_ids"]

#     action = callback.data[5:]  # strip "msel_"

#     if action == "done":
#         await callback.answer()
#         # Build participant list from selected members
#         sel_set = set(selected_ids)
#         participants = [
#             {
#                 "name": m["first_name"]
#                 + (f" {m['last_name']}" if m.get("last_name") else ""),
#                 "tg_user_id": m["tg_user_id"],
#             }
#             for m in members
#             if m["tg_user_id"] in sel_set
#         ]
#         await _finish_creation(
#             callback.message,
#             state,
#             participants,
#             callback.from_user.id,
#             callback.from_user.first_name,
#         )
#         return

#     if action == "add_manual":
#         await state.set_state(MeetCreate.participants)
#         await callback.message.edit_text(
#             "✍️ Перечислите дополнительных участников через запятую:"
#         )
#         await callback.answer()
#         return

#     # Toggle individual member
#     try:
#         uid = int(action)
#     except ValueError:
#         await callback.answer()
#         return

#     if uid in selected_ids:
#         selected_ids.remove(uid)
#     else:
#         selected_ids.append(uid)

#     await state.update_data(selected_ids=selected_ids)
#     await callback.message.edit_reply_markup(
#         reply_markup=_members_select_kb(members, selected_ids)
#     )
#     await callback.answer()


# # ── participants (manual text input) ──────────────────────────────────────────


# @router.message(MeetCreate.participants, F.text)
# async def step_participants(message: Message, state: FSMContext):
#     names = [p.strip() for p in re.split(r"[,\n]+", message.text) if p.strip()]
#     participants = [{"name": n, "tg_user_id": None} for n in names]
#     await _finish_creation(
#         message,
#         state,
#         participants,
#         message.from_user.id,
#         message.from_user.first_name,
#     )


# ── shared creation logic ─────────────────────────────────────────────────────


async def _finish_creation(
    target,  # Message or callback.message — both have .answer() / .chat
    state: FSMContext,
    participants: list[dict],  # [{"name": str, "tg_user_id": int | None}]
    creator_id: int,
    creator_name: str,
) -> None:
    data = await state.get_data()
    await state.clear()

    t_from: str = data.get("time_from", "09:00")
    t_to: str = data.get("time_to", "18:00")
    utc_offset: int = data.get("utc_offset", 3)
    tz_label: str = data.get("tz_label", f"UTC+{utc_offset}")

    data_range = _build_data_range(
        data["date_from"], data["date_to"], t_from, t_to, utc_offset
    )

    try:
        result = await termeet_client.create_meeting(
            name=data["name"],
            data_range=data_range,
            description=data.get("description"),
            duration=data.get("duration"),
        )
    except Exception as e:
        await target.answer(f"❌ Ошибка при создании встречи: {e}")
        return

    hash_ = result["hash"]
    # chat_id = target.chat.id if target.chat.type != "private" else None

    # await db.save_meeting(
    #     hash=hash_,
    #     chat_id=chat_id,
    #     creator_tg_id=creator_id,
    #     name=data["name"],
    # )
    # await db.add_participant(hash_, creator_name, creator_id)
    # for p in participants:
    #     await db.add_participant(hash_, p["name"], p.get("tg_user_id"))

    url = meeting_url(hash_)
    # names = [p["name"] for p in participants]
    text = (
        f"✅ <b>Встреча создана!</b>\n\n"
        f"📅 {data['name']}\n"
        f"📆 {data['date_from']} — {data['date_to']}\n"
        f"🕐 {t_from} – {t_to} ({tz_label})\n"
        f"⏱ {data.get('duration', '—')}\n"
        f"\n🔗 <a href='{url}'>Открыть на сайте</a>\n"
        f"🆔 <code>{hash_}</code>"
    )
    # if names:
    #     text += f"\n\n👥 Участники: {', '.join(names)}"

    await target.answer(text)

    # if chat_id and names:
    #     await target.answer(
    #         f"📣 {', '.join(names)} — заполните слоты для «{data['name']}»:\n"
    #         f"{url}\n\nИли используйте команду /my_slots"
    #     )
