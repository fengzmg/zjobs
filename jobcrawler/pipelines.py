# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
# from pymongo import MongoClient
from scrapy.exceptions import DropItem
from scrapy import log
import app.config as config
import datetime
from jobcrawler.items import JobItem
#import traceback


class ItemPrintingPipeline(object):
    def process_item(self, item, spider):
        log.msg('[%s] Job Title: %s' % (spider.name, item.get('job_title', '--')))
        return item


class ItemDuplicationCheckPipeline(object):
    def process_item(self, item, spider):        
        if JobItem.is_exists(item):
            raise DropItem('Duplicated Job title. Removing...')
        else:
            return item         

class ItemRecuritValidationPipeline(object):
    def process_item(self, item, spider):
        pattern = config.JOB_RULE_OUT_PATTERN
        match = re.search(pattern, item.get('job_title', ''))
        if match is None:
            return item
        else:
            raise DropItem('Job is not posted by recuriter. Removing...')


class ItemPostedByAgentPipeline(object):
    def process_item(self, item, spider):
        pattern = config.AGENT_RULE_OUT_PATTERN
        match = re.search(pattern, item.get('job_title', ''))
        if match is None:
            return item
        else:
            raise DropItem('Job is posted by Agent. Removing...')

class ItemPublishDateFilterPipeline(object):
    def process_item(self, item, spider):
        publish_date = item.get('publish_date', None)
        if publish_date is None:
            raise DropItem('Job has no publish_date...')
        
        if (datetime.datetime.now() - publish_date).days > int(config.HOUSEKEEPING_RECORD_ORDLER_THAN):
            raise DropItem('Job is published order than %s days. Removing...' % str(config.HOUSEKEEPING_RECORD_ORDLER_THAN))
        
        return item

class ItemSaveToDBPipeline(object):
    def process_item(self, item, spider):
        try:
            JobItem.save(item)
        except:
            raise DropItem('Unable to save the job: %s' % item.get('job_title', '--'))
        return item