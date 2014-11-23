# -*- coding: utf-8 -*-

# Scrapy settings for jobcrawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
# http://doc.scrapy.org/en/latest/topics/settings.html
#
import config

BOT_NAME = 'jobcrawler'

SPIDER_MODULES = ['jobcrawler.spiders']
NEWSPIDER_MODULE = 'jobcrawler.spiders'

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'
DEFAULT_REQUEST_HEADERS = {
    'Referer': 'http://zinthedream.appspot.com'
}

ITEM_PIPELINES = {
    'jobcrawler.pipelines.ItemRecuritValidationPipeline': 1,
    'jobcrawler.pipelines.ItemPostedByAgentPipeline': 2,
    'jobcrawler.pipelines.ItemPrintingPipeline': 3,
    'jobcrawler.pipelines.ItemSaveToDBPipeline': 4
}

LOG_LEVEL = 'INFO'

if config.EXPORT_TO_FILE_ENABLED:
    FEED_FORMAT = 'csv'
    FEED_URI = 'file://' + config.APP_HOME + '/crawled_jobs_%(name)s.csv'

CONCURRENT_REQUESTS = 200
COOKIES_ENABLED = False
DOWNLOAD_DELAY = 0
RETRY_ENABLED = False
DOWNLOAD_TIMEOUT = 15

