# -*- coding: utf-8 -*-
import os
from os.path import dirname, realpath
import sys
app_home_dir = dirname(dirname(realpath(__file__)))
sys.path.append(app_home_dir)  # setup sys path to use the current app modules

from multiprocessing import Pool
import datetime
import time
from apscheduler.triggers.cron import CronTrigger
from app.context import logger, Datasource, Scheduler
import app.config as config
from jobcrawler.models import JobItem


class CrawlerRunner:
    def _crawl(cls, spider_name=None):
        if spider_name:
            os.system('cd %s && scrapy crawl %s' % (app_home_dir, spider_name))
            logger.info('Done running spider %s' % spider_name)
        return None

    def __call__(self, *args, **kwargs):
        self._crawl(args[0])


class AppRunner(object):

    instance = None
    datasource = Datasource.get_instance()

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = AppRunner()
        return cls.instance

    @classmethod
    def create_db(cls):
        conn = cls.datasource.get_connection()
        try:
            c = conn.cursor()

            c.execute('DROP TABLE IF EXISTS CRAWLED_JOBS')
            c.execute('DROP INDEX IF EXISTS job_title_idx')

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
                )
                ''')

            c.execute('''
                CREATE UNIQUE INDEX job_title_idx ON CRAWLED_JOBS(job_title)
            ''')

            logger.info("created table and indexes for CRAWLED_JOBS")

            c.execute('DROP TABLE IF EXISTS JOB_REJECTION_RULES')
            c.execute('DROP INDEX IF EXISTS reject_pattern_idx')

            c.execute('''
                CREATE TABLE IF NOT EXISTS JOB_REJECTION_RULES(
                    reject_pattern    text,
                    reject_reason     text
                )
                ''')

            c.execute('''
                CREATE UNIQUE INDEX reject_pattern_idx ON JOB_REJECTION_RULES(reject_pattern)
            ''')

            logger.info("created table and indexes for JOB_REJECTION_RULES")

            c.execute('DROP TABLE IF EXISTS BLOCKED_CONTACTS')
            c.execute('DROP INDEX IF EXISTS blocked_contacts_idx')

            c.execute('''
                CREATE TABLE IF NOT EXISTS BLOCKED_CONTACTS(
                    contact    text,
                    block_reason text
                )
                ''')

            c.execute('''
                CREATE UNIQUE INDEX blocked_contacts_idx ON BLOCKED_CONTACTS(contact)
            ''')

            logger.info("created table and indexes for BLOCKED_CONTACTS")

            conn.commit()
            logger.info('done create database')
        except Exception as e:
            logger.error('Unable to run create_db')
            logger.error(e)
            conn.rollback()

        finally:
            conn.close()

    @classmethod
    def migrate_db(cls):
        """
        place holder for putting the migrate db scripts -- need to be updated before every release
        :return:
        """

        cls.create_db()
        conn = cls.datasource.get_connection()
        try:
            logger.info('start migrating database')
            logger.info('done migrating database')
        except Exception as e:
            logger.error('Unable to run migrate_db')
            logger.error(e)

        finally:
            conn.close()


    @classmethod
    def run_crawler(cls):
        start_time = time.time()
        logger.info('start running crawler..')

        # os.system('python '+ app_home_dir +'/app/run_crawler.py')
        spider_names = ['sgxin', 'shichengbbs', 'singxin', 'sggongzuo']

        pool = Pool(processes=len(spider_names))
        pool.map(CrawlerRunner(), spider_names)

        logger.info('done running crawler.. Time elapsed: %.3fs' % (time.time() - start_time))


    @classmethod
    def run_web(cls):
        logger.info('starting web..')
        os.system('cd ' + app_home_dir + ' && gunicorn -c app/gunicorn.conf.py web.jobboard:app --debug')

    @classmethod
    def run_flask_web(cls):
        import web.jobboard

        web.jobboard.app.run(host='0.0.0.0', port=config.WEB_HTTP_PORT, debug=config.WEB_DEBUG_ENABLED)

    @classmethod
    def run_heartbeater(cls):
        import requests

        logger.info('started heartbeating..')
        resp = requests.get(config.APP_HEARTBEAT_URL, headers={'User-Agent': 'Zjobs Heartbeater'})
        logger.info('heartbeater received status_code %s', resp.status_code)
        logger.info('done hearting beating')

    @classmethod
    def run_housekeeper(cls):
        logger.info('start running housekeeper..')
        logger.info('start removing records older than 14 days..')
        JobItem.remove_old_records(retention_days=config.HOUSEKEEPING_RECORD_ORDLER_THAN)
        logger.info('done removing records older than 14 days..')

        logger.info('start removing records posted by blocked contacts..')
        JobItem.remove_blocked_records()
        logger.info('done removing records posted by blocked contacts..')

        logger.info('start removing records should have been rejected..')
        JobItem.remove_records_matches_rejection_pattern()
        logger.info('done removing records should have been rejected..')

        logger.info('done running housekeeper..')


    @classmethod
    def run_emailer(cls):
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email import Encoders
        import smtplib

        logger.info('start sending email to subscribers...')
        smtp = smtplib.SMTP(host=config.SMTP_HOST, port=config.SMTP_PORT)

        try:
            smtp.set_debuglevel(4)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(user=config.SMTP_USER, password=config.SMTP_PASSWORD)

            logger.info('established secure connection to smtp server...')

            toaddrs = config.TO_ADDRS
            fromaddr = config.FROM_ADDR

            current_date_string = datetime.datetime.now().strftime('%Y-%m-%d')
            message_subject = "%s:%s" % (config.APP_NAME, current_date_string)
            message_text = "Thank you for subscribing %s. Please find the newly posted jobs as of %s" % (
                config.APP_NAME, current_date_string)

            msg = MIMEMultipart()
            msg['From'] = fromaddr
            msg['To'] = ','.join(toaddrs)
            msg['Subject'] = message_subject
            msg.attach(MIMEText(message_text))

            part = MIMEBase('application', "octet-stream")
            file_format = 'xlsx'
            part.set_payload(JobItem.extract_records_as_bytes(file_format))
            logger.info('attached extracted files to the mail...waiting to be sent..')
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment; filename="extracted_jobs_%s.%s"' % (current_date_string, file_format))
            msg.attach(part)

            smtp.sendmail(fromaddr, toaddrs, msg.as_string())
            logger.info('done sending email to subscribers...')
        except Exception as e:
            logger.error(e)
        finally:
            smtp.quit()


    @classmethod
    def run_batch_jobs(cls):
        scheduler = Scheduler.get_scheduler()
        scheduler.add_job(func=cls.run_crawler, trigger=CronTrigger(hour='*/04'))
        scheduler.add_job(func=cls.run_housekeeper, trigger=CronTrigger(hour='23', minute='05'))
        scheduler.add_job(func=cls.run_heartbeater, trigger=CronTrigger(minute='*/30'))
        scheduler.add_job(func=cls.run_emailer, trigger=CronTrigger(hour='23', minute='35'))

    @classmethod
    def run_app(cls):
        cls.run_batch_jobs()
        cls.run_web()


def parse_process_args():
    import argparse

    parser = argparse.ArgumentParser('run the app component')
    parser.add_argument('component', nargs='?', default='all', type=str,
                        help='app component to run. [all|web|flask_web|batch_jobs|crawler|housekeeper|heartbeater|emailer|migrate_db]')
    args = parser.parse_args()

    if args.component is None:
        AppRunner.run_app()
    elif args.component == 'all':
        AppRunner.run_app()
    elif args.component == 'batch_jobs':
        AppRunner.run_batch_jobs()
    elif args.component == 'crawler':
        AppRunner.run_crawler()
    elif args.component == 'housekeeper':
        AppRunner.run_housekeeper()
    elif args.component == 'heartbeater':
        AppRunner.run_heartbeater()
    elif args.component == 'web':
        AppRunner.run_web()
    elif args.component == 'flask_web':
        AppRunner.run_flask_web()
    elif args.component == 'migrate_db':
        AppRunner.migrate_db()
    elif args.component == 'emailer':
        AppRunner.run_emailer()
    else:
        print 'Invalid Usage: '
        parser.print_help()


if __name__ == '__main__':
    parse_process_args()