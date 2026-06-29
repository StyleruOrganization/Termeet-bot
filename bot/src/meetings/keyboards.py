from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def time_window_kb() -> InlineKeyboardMarkup:
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


def timezone_kb() -> InlineKeyboardMarkup:
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


def duration_kb() -> InlineKeyboardMarkup:
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
