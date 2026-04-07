from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.time import APP_TIMEZONE
from app.db.session import AsyncSessionLocal
from app.services.alert_evaluator import evaluate_alerts


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_evaluation_job() -> None:
    async with AsyncSessionLocal() as session:
        result = await evaluate_alerts(session)
    logger.info(
        "Alert evaluation finished: alerts=%s matched=%s notifications=%s",
        result.evaluated_alerts,
        result.matched_forecasts,
        result.created_notifications,
    )


async def main() -> None:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone=APP_TIMEZONE)
    scheduler.add_job(
        run_evaluation_job,
        trigger=CronTrigger.from_crontab(settings.alert_evaluation_cron, timezone=APP_TIMEZONE),
        id="weather-alert-evaluation",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Worker scheduler started with cron '%s'", settings.alert_evaluation_cron)

    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
