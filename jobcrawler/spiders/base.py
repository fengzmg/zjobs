# -*- coding: utf-8 -*-
from scrapy.contrib.spiders.crawl import CrawlSpider
from scrapy.http.request import Request
from jobcrawler.items import JobItem
import app.config as config
from scrapy import log
import re

class BaseSpider(CrawlSpider):
    name = "base"
    allowed_domains = []
    start_urls = ()

    rules = ()

    def parse_start_url(self, response):
        return self.parse_item(response)


    def parse_item(self, response):
        return self.parse_item_requests_callback(response, '')
        

    def parse_item_requests_callback(self, response, item_xpath_selector=''):
        requests = []
        for job_item in response.xpath(item_xpath_selector):

            job_crawler_item = JobItem()
            self.populate_job_crawler_item(job_item, job_crawler_item)

            if self.should_load_details(job_crawler_item):
                requests.append(
                    Request(url=job_crawler_item.get('job_details_link', ''), callback=self.retrieve_job_details,
                            meta={'item': job_crawler_item}, dont_filter=True))

        return requests


    def populate_job_crawler_item(self, detail_item, job_crawler_item):
        pass

    def retrieve_job_details(self, response):
        yield None

    def should_load_details(self, job_item):
        if JobItem.is_exists(job_item):
            log.msg('skipping loading details as job already exists. job_title: %s' % job_item.get('job_title', ''))
            return False
        if re.search(config.AGENT_RULE_OUT_PATTERN, job_item.get('job_title', '')):
            log.msg('skipping loading details as job is posted by agent. job_title: %s' % job_item.get('job_title', ''))
            return False

        if re.search(config.JOB_RULE_OUT_PATTERN, job_item.get('job_title', '')):
            log.msg('skipping loading details as job is invalid. job_title: %s' % job_item.get('job_title', ''))
            return False

        return True





