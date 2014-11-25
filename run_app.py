from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from run_web import run_web
from run_housekeeping import run_housekeeping
from apscheduler.schedulers.background import BackgroundScheduler
import os
def run_crawler_script():
    os.system('python run_crawler.py')

def start_scheduler():
    executors = {
        'default': ThreadPoolExecutor(2),
        'processpool': ProcessPoolExecutor(2)
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }
    scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)
    crawler_trigger = CronTrigger(hour='*/12')
    #crawler_trigger = CronTrigger(minute='*/05')
    hourse_keeping_trigger = CronTrigger(hour='12', minute='30')

    scheduler.add_job(func=run_crawler_script, trigger=crawler_trigger)
    scheduler.add_job(func=run_housekeeping, trigger=hourse_keeping_trigger)
    scheduler.start()


def run():
    start_scheduler()
    run_web()

if __name__ == '__main__':
    run()