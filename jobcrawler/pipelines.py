# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
from scrapy.exceptions import DropItem
from scrapy import log
import app.config as config
from jobcrawler.items import JobItem, BlockedContact


class ItemPrintingPipeline(object):
    def process_item(self, item, spider):
        log.msg('[%s] Job Title: %s' % (spider.name, item.job_title))
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
        match = re.search(pattern, item.job_title)
        if match is None:
            return item
        else:
            raise DropItem('Job is not posted by recuriter. Removing...')


class ItemPostedByAgentPipeline(object):
    def process_item(self, item, spider):
        # check by title
        pattern = config.AGENT_RULE_OUT_PATTERN
        match = re.search(pattern, item.job_title)
        if match:
            raise DropItem('Job is posted by Agent based on job title. Removing...')

        # check by contact
        if BlockedContact.is_contact_blocked(item.contact):
            raise DropItem('Job is posted by blocked contact. Removing...')

        return item

class ItemPublishDateFilterPipeline(object):
    def process_item(self, item, spider):

        if JobItem.is_older_required(item):
            raise DropItem(
                'Job is published order than %s days. Removing...' % str(config.HOUSEKEEPING_RECORD_ORDLER_THAN))

        return item

class ItemFieldFormatValidationPipeline(object):
    def process_item(self, item, spider):
        # validate the contact format
        if item.contact and item.contact != '' and not re.match(r"[0-9]+", item.contact):
            item.contact = ''  # set the contact to empty

        return item


class ItemSaveToDBPipeline(object):
    def process_item(self, item, spider):
        try:
            JobItem.save(item)
        except:
            raise DropItem('Unable to save the job: %s' % item.job_title)
        return item