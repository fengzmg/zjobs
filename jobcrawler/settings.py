# -*- coding: utf-8 -*-

# Scrapy settings for jobcrawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
# http://doc.scrapy.org/en/latest/topics/settings.html
#
from scrapy import log
from scrapy import logformatter
from app.context import Config


class PoliteLogFormatter(logformatter.LogFormatter):
    def dropped(self, item, exception, response, spider):
        return {
            'level': log.WARNING,
            'format': u"Dropped: %(exception)s",
            'exception': exception,
            'item': None,
        }


BOT_NAME = 'jobcrawler'

SPIDER_MODULES = ['jobcrawler.spiders']
NEWSPIDER_MODULE = 'jobcrawler.spiders'

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'
DEFAULT_REQUEST_HEADERS = {
    'Referer': 'http://zinthedream.appspot.com'
}

ITEM_PIPELINES = {

    'jobcrawler.pipelines.ItemRejectionPatternPipeline': 1,
    'jobcrawler.pipelines.ItemBlockedContactPipeline': 2,
    'jobcrawler.pipelines.ItemDuplicationCheckPipeline': 3,
    'jobcrawler.pipelines.ItemPublishDateFilterPipeline': 4,
    'jobcrawler.pipelines.ItemFieldFormatValidationPipeline': 5,
    'jobcrawler.pipelines.ItemPrintingPipeline': 6,
    'jobcrawler.pipelines.ItemSaveToDBPipeline': 7
}

LOG_LEVEL = 'INFO'
LOG_FORMATTER = 'jobcrawler.settings.PoliteLogFormatter'
LOG_FILE = Config.LOG_FILE
LOG_ENABLED = False
CONCURRENT_REQUESTS = 200
COOKIES_ENABLED = False
DOWNLOAD_DELAY = 0
RETRY_ENABLED = False
DOWNLOAD_TIMEOUT = 30


