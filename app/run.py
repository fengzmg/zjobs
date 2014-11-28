
import os
from os.path import dirname, realpath
import sys

app_home_dir = dirname(dirname(realpath(__file__)))
sys.path.append(app_home_dir)  ### setup sys path to use the current app modules

import app.config as config
import logging
import pg8000 as dbi

logger = logging.getLogger('zjobs.backend')
logger.setLevel(logging.INFO)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

def run_crawler():
    logger.info('start running crawler..')
    os.system('python '+ app_home_dir +'/app/run_crawler.py')
    logger.info('done running crawler..')

def run_web():
    logger.info('starting web..')
    os.system('cd '+ app_home_dir +' && gunicorn -c app/gunicorn.conf.py web.jobboard:app --debug')

def run_flask_web():
    import web.jobboard
    web.jobboard.app.run(host='0.0.0.0', port=config.WEB_HTTP_PORT, debug=config.WEB_DEBUG_ENABLED)

def run_heartbeater():
    import urllib

    logger.info('scheduler started heartbeating..')
    resp = urllib.urlopen(config.APP_HEARTBEAT_URL)
    resp.read()
    logger.info('scheduler done hearting beating')

def run_housekeeper():
    
    def remove_old_records():
        conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
        c = conn.cursor()
        c.execute("DELETE FROM CRAWLED_JOBS WHERE publish_date < NOW() - INTERVAL '" + str(config.HOUSEKEEPING_RECORD_ORDLER_THAN) +" days'")
        conn.commit()
        conn.close()

    logger.info('start running housekeeper..')
    remove_old_records()
    logger.info('done running housekeeper..')


def run_scheduler():
    from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.schedulers.background import BackgroundScheduler

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

    scheduler.add_job(func=run_crawler, trigger=crawler_trigger)
    scheduler.add_job(func=run_housekeeper, trigger=hourse_keeping_trigger)
    scheduler.add_job(func=run_heartbeater, trigger=heartbeat_trigger)
    
    scheduler.start()
    logger.info('scheduler is started')


def run_app():
    run_scheduler()
    run_web()

def parse_process_args():
    import argparse
    parser = argparse.ArgumentParser('run the app component')
    parser.add_argument('-c', '--component', type=str,  help='app component to run. [all|web|flask_web|scheduler|crawler|housekeeper|heartbeater]')
    args = parser.parse_args()

    if args.component == 'all':
        run_app()
    elif args.component == 'scheduler':
        run_scheduler()
    elif args.component == 'crawler':
        run_crawler()
    elif args.component == 'housekeeper':
        run_housekeeper()
    elif args.component == 'heartbeater':
        run_heartbeater()
    elif args.component == 'web':
        run_web()
    elif args.component == 'flask_web':
        run_flask_web()

    else:
        print 'Invalid Usage: '
        parser.print_help()

if __name__ == '__main__':

    parse_process_args()