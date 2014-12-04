# -*- coding: utf-8 -*-
import datetime
from scrapy.contrib.spiders.crawl import Rule
from scrapy.contrib.linkextractors import LinkExtractor
from jobcrawler.spiders.base import BaseSpider

class SingxinSpider(BaseSpider):
    name = "singxin"
    allowed_domains = ["singxin.com"]
    start_urls = (
        'http://www.singxin.com/category/view/id/47',
    )

    rules = (
        Rule(LinkExtractor(allow='/category/view/id/47/page/[0-3]'), callback='parse_item', follow=True, ),
    )

    def parse_start_url(self, response):
        return self.parse_item(response)


    def parse_item(self, response):
        return self.parse_item_requests_callback(response, '//div[@class="listCell"]')

    def populate_job_crawler_item(self, detail_item, job_crawler_item):
        try:
            job_crawler_item['job_title'] = detail_item.xpath('.//a[@class="title"]/text()').extract()[0]
            job_crawler_item['job_details_link'] = 'http://www.singxin.com' + detail_item.re(r'<a.*href="(/info/view/id/[0-9]+)">.*</a>')[0]
            job_crawler_item['job_country'] = 'Singapore'
            job_crawler_item['job_location'] = 'Singapore'
            job_crawler_item['contact'] = detail_item.re(r'<a.*href="tel:(.*)">.*</a>')[0]
            job_crawler_item['source'] = self.name
            job_crawler_item['crawled_date'] = datetime.datetime.now()

        except Exception as e:
            print e


    def retrieve_job_details(self, response):
        job_crawler_item = response.meta['item']

        try:
            job_crawler_item['job_desc'] = response.xpath('/html/head/meta[@name="description"]/@content').extract()[0]

            job_crawler_item['publish_date'] = response.selector.re('<td><i class="icon-calendar icon-small"></i>(.*)</td>')[0].replace(' ', '')
            
            #Convert to the datetime format
            job_crawler_item['publish_date'] = datetime.datetime.strptime(job_crawler_item.get('publish_date'), '%Y-%m-%d') if job_crawler_item.get('publish_date', None) is not None else None
        except Exception as e:
            print e

        yield job_crawler_item




