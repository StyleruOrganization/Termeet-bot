import re
from datetime import date, timedelta

TIME_PRESETS: dict[str, tuple[str, str]] = {
    "tw_0918": ("09:00", "18:00"),
    "tw_0919": ("09:00", "19:00"),
    "tw_1018": ("10:00", "18:00"),
    "tw_1020": ("10:00", "20:00"),
}

TZ_PRESETS: dict[str, tuple[int, str]] = {
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


def parse_date(text: str) -> date | None:
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


def build_data_range(
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
