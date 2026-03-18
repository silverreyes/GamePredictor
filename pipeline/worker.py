"""APScheduler-based worker entrypoint for Docker container."""
import os
import signal
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from pipeline.refresh import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler()


def shutdown(signum, frame):
    logger.info("Received signal %s, shutting down scheduler...", signum)
    scheduler.shutdown(wait=True)


def main():
    cron_hour = int(os.environ.get("REFRESH_CRON_HOUR", "6"))
    scheduler.add_job(
        run_pipeline,
        CronTrigger(day_of_week="tue", hour=cron_hour, timezone="UTC"),
        id="weekly_refresh",
        max_instances=1,
        replace_existing=True,
    )
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    logger.info("Worker started. Next refresh: Tuesday %02d:00 UTC", cron_hour)
    scheduler.start()


if __name__ == "__main__":
    main()
