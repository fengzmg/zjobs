
import os
from os.path import dirname, realpath
import sys

app_home_dir = dirname(dirname(realpath(__file__)))
sys.path.append(app_home_dir)  ### setup sys path to use the current app modules

import app.config as config
import pg8000 as dbi
from app.config import logger
from jobcrawler.items import JobItem

def create_db():
    #conn = sqlite3.connect(config.DB_FILE)
    conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
    #conn = dbi.connect('postgres://zjobs:zjobs@localhost:5432/zjobs')
    try:
        c = conn.cursor()

        c.execute('DROP TABLE IF EXISTS CRAWLED_JOBS')
        c.execute('DROP INDEX IF EXISTS job_title_idx')

        logger.info("dropped related tables and indexes")

        # c.execute('''
        #     CREATE TABLE IF NOT EXISTS CRAWLED_JOBS(
        #         source            text,
        #         crawled_date      timestamp,
        #         publish_date      timestamp,
        #         job_title         text,
        #         job_desc          text,
        #         job_details_link  text,
        #         job_location      text,
        #         job_country       text,
        #         salary            text,
        #         employer_name     text,
        #         contact           text
        #     );
        # ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS CRAWLED_JOBS(
                source            text,
                crawled_date      date,
                publish_date      date,
                job_title         text,
                job_desc          text,
                job_details_link  text,
                job_location      text,
                job_country       text,
                salary            text,
                employer_name     text,
                contact           text
            );
            ''')

        logger.info("created related tables")

        c.execute('''
            CREATE UNIQUE INDEX job_title_idx ON CRAWLED_JOBS(job_title)
        ''')

        logger.info("created related indexes")

        conn.commit()
        logger.info('done create database')
    except:
        conn.rollback()
        logger.error('Unable to run create_db')
    finally:
        conn.close()
    

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

    logger.info('start running housekeeper..')
    JobItem.remove_old_records(retention_days=config.HOUSEKEEPING_RECORD_ORDLER_THAN)
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

    if args.component is None:
        run_app()
    elif args.component == 'all':
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
    elif args.component == 'create_db':
        create_db()
    else:
        print 'Invalid Usage: '
        parser.print_help()

if __name__ == '__main__':
    parse_process_args()