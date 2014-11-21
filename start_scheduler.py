from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from run_crawler import run_crawler

from apscheduler.schedulers.blocking import BlockingScheduler


def start_scheduler():
    executors = {
        'default': ThreadPoolExecutor(2),
        'processpool': ProcessPoolExecutor(2)
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }
    scheduler = BlockingScheduler(executors=executors, job_defaults=job_defaults)
    trigger = CronTrigger(hour='22', minute='30')
    scheduler.add_job(func=run_crawler, trigger=trigger)
    scheduler.start()


def run():
    start_scheduler()

if __name__ == '__main__':
    run()