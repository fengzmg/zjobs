import logging
import app.config as config
from apscheduler.schedulers.background import BackgroundScheduler
import pg8000 as dbi

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