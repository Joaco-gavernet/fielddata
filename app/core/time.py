from datetime import datetime
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")


def now_tz() -> datetime:
    return datetime.now(APP_TIMEZONE)
