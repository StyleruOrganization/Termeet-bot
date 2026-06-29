import re
import random
from typing import TYPE_CHECKING

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.context import FSMContext

from bot.src.meetings.api import termeet_client
from bot.src.meetings.utils import parse_date, build_data_range, TIME_PRESETS, TZ_PRESETS
from bot.src.meetings.keyboards import duration_kb, timezone_kb, time_window_kb
from bot.src.metrics import create_meetings_latency
from bot.src.config import config

if TYPE_CHECKING:
    from bot.src.meetings.schemas import MeetCreateResponse


router = Router()


class MeetCreate(StatesGroup):
    name = State()
    date_from = State()
    date_to = State()
    time_window = State()
    timezone = State()
    duration = State()
    description = State()


@router.message(Command("meet"), StateFilter(default_state))
async def cmd_meet(message: Message, state: FSMContext):
    await state.set_state(MeetCreate.name)
    await message.answer("📅 <b>Создание встречи</b>\n\nКак назовём встречу?")


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
    d = parse_date(message.text)
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
    d = parse_date(message.text)
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
        reply_markup=time_window_kb(),
    )


@router.callback_query(MeetCreate.time_window, F.data.in_(TIME_PRESETS))
async def step_time_window_preset(callback: CallbackQuery, state: FSMContext):
    t_from, t_to = TIME_PRESETS[callback.data]
    await state.update_data(time_from=t_from, time_to=t_to)
    await state.set_state(MeetCreate.timezone)
    await callback.message.edit_text(
        f"✅ Часы: {t_from} – {t_to}\n\n🌍 Выберите ваш часовой пояс:",
        reply_markup=timezone_kb(),
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
            reply_markup=time_window_kb(),
        )
        return
    t_from, t_to = m.group(1), m.group(2)
    await state.update_data(time_from=t_from, time_to=t_to)
    await state.set_state(MeetCreate.timezone)
    await message.answer(
        f"✅ Часы: {t_from} – {t_to}\n\n🌍 Выберите ваш часовой пояс:",
        reply_markup=timezone_kb(),
    )


@router.callback_query(MeetCreate.timezone, F.data.in_(TZ_PRESETS))
async def step_timezone_preset(callback: CallbackQuery, state: FSMContext):
    offset, label = TZ_PRESETS[callback.data]  # Устанваливаем часовой пояс
    await state.update_data(utc_offset=offset, tz_label=label)
    await state.set_state(MeetCreate.duration)
    await callback.message.edit_text(
        f"✅ Часовой пояс: {label}\n\n⏱ Сколько длится встреча?",
        reply_markup=duration_kb(),
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
            reply_markup=timezone_kb(),
        )
        return
    label = f"UTC{offset:+d}"
    await state.update_data(utc_offset=offset, tz_label=label)
    await state.set_state(MeetCreate.duration)
    await message.answer(
        f"✅ Часовой пояс: {label}\n\n⏱ Сколько длится встреча?",
        reply_markup=duration_kb(),
    )


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
    await _finish_creation(
        message,
        state,
    )


async def _finish_creation(
    target,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    await state.clear()

    t_from: str = data.get("time_from", "09:00")
    t_to: str = data.get("time_to", "18:00")
    utc_offset: int = data.get("utc_offset", 3)
    tz_label: str = data.get("tz_label", f"UTC+{utc_offset}")

    data_range = build_data_range(
        data["date_from"], data["date_to"], t_from, t_to, utc_offset
    )

    try:
        if random.random() < 0.5:
            with create_meetings_latency.labels(method="grpc").time():
                result: MeetCreateResponse = await termeet_client.create_meeting_grpc(
                    name=data["name"],
                    data_range=data_range,
                    description=data.get("description"),
                    duration=data.get("duration"),
                )
        else:
            with create_meetings_latency.labels(method="json").time():
                result: MeetCreateResponse = await termeet_client.create_meeting_json(
                    name=data["name"],
                    data_range=data_range,
                    description=data.get("description"),
                    duration=data.get("duration"),
                )
    except Exception:
        await target.answer("❌ Ошибка при создании встречи. Обратитесь к @d10110101 за помощью")
        return

    url = config.telegram.BACKEND_API_URL.rstrip("/") + f"/meet/{result.hash}"

    text = (
        f"✅ <b>Встреча создана!</b>\n\n"
        f"📅 {data['name']}\n"
        f"📆 {data['date_from']} — {data['date_to']}\n"
        f"🕐 {t_from} – {t_to} ({tz_label})\n"
        f"⏱ {data.get('duration', '—')}\n"
        f"\n🔗 <a href='{url}'>Открыть на сайте:</a>\n"
        f"🆔 <a href='{url}'>{url}</a>"
    )

    await target.answer(text)
