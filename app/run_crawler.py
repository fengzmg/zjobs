
import os
from os.path import dirname, realpath
import sys

app_home_dir = dirname(dirname(realpath(__file__)))
sys.path.append(app_home_dir)  ### setup sys path to use the current app modules

from scrapy.xlib.pydispatch import dispatcher
import app.config as config
from jobcrawler.spiders.sgxin import SgxinSpider

from jobcrawler.spiders.shichengbbs import ShichengBBSSpider
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import Encoders
from scrapy.crawler import Crawler
from scrapy.utils.project import get_project_settings
from scrapy import log, signals
from twisted.internet import reactor
import smtplib
# import sqlite3 as dbi
import pg8000 as dbi

def setup_crawler(spider_types):
    assert type(spider_types) is list

    spider_names = []
    for spider_type in spider_types:
        settings = get_project_settings()
        spider = spider_type()

        if config.EXPORT_TO_FILE_ENABLED:
            file_to_remove = '/apps/jobcrawler/crawled_jobs_%s.csv' % spider.name
            os.remove(file_to_remove) if os.path.exists(file_to_remove) else None

        crawler = Crawler(settings)
        crawler.configure()
        crawler.crawl(spider)
        crawler.start()

        spider_names.append(spider.name)
    return spider_names


def send_results(spider_names):
    smtp = smtplib.SMTP(host=config.SMTP_HOST, port=config.SMTP_PORT)
    smtp.set_debuglevel(4)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(user=config.SMTP_USER, password=config.SMTP_PASSWORD)

    toaddrs = config.TO_ADDRS
    fromaddr = config.FROM_ADDR

    for spider_name in spider_names:
        message_subject = "Crawled Result From %s" % spider_name
        message_text = "Please find the crawled result for %s" % spider_name
        file_to_attach = config.APP_HOME + '/crawled_jobs_%s.csv' % spider_name

        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = ','.join(toaddrs)
        msg['Subject'] = message_subject
        msg.attach(MIMEText(message_text))

        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(file_to_attach, "rb").read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file_to_attach))
        msg.attach(part)

        smtp.sendmail(fromaddr, toaddrs, msg.as_string())

    smtp.quit()


def stop_reactor():
    stop_reactor.spider_closed_count += 1
    reactor.stop() if stop_reactor.spider_closed_count == stop_reactor.spider_count else None

def refresh_database():
    #conn = dbi.connect(config.DB_FILE)
    conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
    c = conn.cursor()
    c.execute('DELETE FROM CRAWLED_JOBS')
    conn.commit()
    conn.close()

def run_crawler():

    if config.REFRESH_DB_ENABLED:
        refresh_database()

    spider_names = setup_crawler(spider_types=[SgxinSpider, ShichengBBSSpider])
    stop_reactor.spider_count = 2
    stop_reactor.spider_closed_count = 0
    dispatcher.connect(stop_reactor, signals.spider_closed)
    log.start()
    reactor.run()

    send_results(spider_names) if config.SEND_EMAIL_ENABLED else None


if __name__ == '__main__':
    run_crawler()