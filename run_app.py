from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from run_housekeeping import run_housekeeping
from apscheduler.schedulers.background import BackgroundScheduler
import os
import urllib
import config
import logging

logger = logging.getLogger('apscheduler')
logger.setLevel(logging.INFO)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

def run_crawler_script():
    os.system('python run_crawler.py')

def run_web_script():
    os.system('gunicorn -c gunicorn.conf.py web.jobboard:app --debug')

def heartbeat():
    logger.info('scheduler started heartbeating..')
    resp = urllib.urlopen(config.APP_HEARTBEAT_URL)
    resp.read()
    logger.info('scheduler done hearting beating')

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
    crawler_trigger = CronTrigger(hour='*/08')
    #crawler_trigger = CronTrigger(minute='*/05')
    hourse_keeping_trigger = CronTrigger(hour='12', minute='30')

    heartbeat_trigger = CronTrigger(minute='*/30')

    scheduler.add_job(func=run_crawler_script, trigger=crawler_trigger)
    scheduler.add_job(func=run_housekeeping, trigger=hourse_keeping_trigger)
    scheduler.add_job(func=heartbeat, trigger=heartbeat_trigger)
    
    scheduler.start()
    logger.info('scheduler is started')


def run():
    start_scheduler()
    run_web_script()

if __name__ == '__main__':
    run()