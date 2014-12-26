import logging
from apscheduler.schedulers.background import BackgroundScheduler
import pg8000 as dbi
import os

###################################################
#   Logging Configuration  -- config.logger can be imported
##################################################
logger = logging.getLogger('zjobs.backend')
logger.setLevel(logging.INFO)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s] %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

class Config:

    APP_NAME = 'Zjobs'
    APP_HOME = '/apps/jobcrawler'
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DATABASE = os.environ.get('DATABASE', 'zjobs')
    DB_USER = os.environ.get('DB_USER', 'zjobs')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'zjobs')

    FROM_ADDR = 'zorg.groups@gmail.com'

    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', 'zorg.groups@gmail.com')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

    WEB_HTTP_PORT = int(os.environ.get('PORT', 33507))
    WEB_DEBUG_ENABLED = True

    HOUSEKEEPING_RECORD_ORDLER_THAN = 20
    EXPORT_TO_FILE_ENABLED = False

    APP_HEARTBEAT_URL = 'https://zjobs.herokuapp.com/'

config = Config

class Datasource:
    instance = None
    dbi.paramstyle = 'qmark'
    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = Datasource()
        return cls.instance

    @classmethod
    def get_connection(cls):
        conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
        return conn


class Scheduler:
    scheduler = None

    @staticmethod
    def get_scheduler():
        if Scheduler.scheduler is None:
            Scheduler.scheduler = BackgroundScheduler(logger=logger)
            Scheduler.scheduler.start()

        return Scheduler.scheduler
