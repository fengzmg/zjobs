# -*- coding: utf-8 -*-
import datetime
from scrapy.contrib.spiders.crawl import Rule
from scrapy.contrib.linkextractors import LinkExtractor
from jobcrawler.spiders.base import BaseSpider
import re

class SggonguoSpider(BaseSpider):
    name = "sggongzuo"
    allowed_domains = ["gongzuo.sg"]
    start_urls = (
        'http://www.gongzuo.sg',
    )

    rules = (
        Rule(LinkExtractor(allow='/\?page=[0-1]'), callback='parse_item', follow=True, ),
    )

    def parse_start_url(self, response):
        return self.parse_item(response)


    def parse_item(self, response):
        return self.parse_item_requests_callback(response, '//div[@class="summary"]')


    def populate_job_crawler_item(self, detail_item, job_crawler_item):
        try:
            job_crawler_item.job_title = detail_item.xpath('.//div[@class="title"]/a[1]/text()').extract()[0]
            job_crawler_item.job_details_link = detail_item.xpath('.//div[@class="title"]/a[1]/@href').extract()[0]
            job_crawler_item.job_country = 'Singapore'
            job_crawler_item.job_location = 'Singapore'
            job_crawler_item.publish_date = re.search(r'.*([0-9]{4}-[0-9]{2}-[0-9]{2}).*', detail_item.xpath('.//div[@class="attr"]/text()[2]').extract()[0], re.M).group(1).strip()
            #Convert to the datetime format
            job_crawler_item.publish_date = datetime.datetime.strptime(job_crawler_item.publish_date, '%Y-%m-%d') if job_crawler_item.publish_date is not None else None
            job_crawler_item.salary = detail_item.xpath('.//div[@class="attr"]/text()[4]').extract()[0].replace(',','').strip()
            job_crawler_item.source = self.name
            job_crawler_item.crawled_date = datetime.datetime.now()

        except Exception as e:
            print e

    def retrieve_job_details(self, response):
        job_crawler_item = response.meta['item']

        try:
            job_crawler_item.job_desc = response.xpath('/html/head/meta[@name="description"]/@content').extract()[0]
            job_crawler_item.contact = response.xpath('//div[@id="article-body"]/div[@class="attr"]/text()[3]').extract()[0].replace('\n', '').strip()
        except Exception as e:
            print e

        yield job_crawler_item




