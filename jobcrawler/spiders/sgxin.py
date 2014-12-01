# -*- coding: utf-8 -*-
import datetime
from scrapy.contrib.spiders.crawl import CrawlSpider, Rule
from scrapy.http.request import Request
from scrapy.contrib.linkextractors import LinkExtractor

from jobcrawler.items import JobItem
import re


class SgxinSpider(CrawlSpider):
    name = "sgxin"
    allowed_domains = ["sgxin.com"]
    start_urls = (
        'http://www.sgxin.com/viewcat_job1.html',
        'http://www.sgxin.com/viewcat_job2.html',
        'http://www.sgxin.com/viewcat_job3.html',
        'http://www.sgxin.com/viewcat_job4.html',
        'http://www.sgxin.com/viewcat_job5.html',
        'http://www.sgxin.com/viewcat_job6.html',
        'http://www.sgxin.com/viewcat_job7.html',
        'http://www.sgxin.com/viewcat_job8.html',
        'http://www.sgxin.com/viewcat_job9.html',
        'http://www.sgxin.com/viewcat_job10.html',
    )

    rules = (
        Rule(LinkExtractor(allow='index\.php\?ct=job.*&md=browse&page=[0-1]&'), callback='parse_item'),
    )

    def parse_start_url(self, response):
        return self.parse_item(response)


    def parse_item(self, response):
        requests = []
        for job_item in response.xpath('//tr'):
            job_crawler_item = JobItem()
            for index, detail_item in enumerate(job_item.xpath('./td')):
                self.populate_job_crawler_item(index, detail_item, job_crawler_item)
                if index == 4:
                    requests.append(
                        Request(url=job_crawler_item.get('job_details_link', ''), callback=self.retrieve_job_details,
                                meta={'item': job_crawler_item}, dont_filter=True))

        return requests

    def populate_job_crawler_item(self, index, detail_item, job_crawler_item):

        if index == 0:
            self.populate_job_title(detail_item, job_crawler_item)
        elif index == 1:
            self.populate_salary(detail_item, job_crawler_item)
        elif index == 2:
            self.populate_employer_name(detail_item, job_crawler_item)
        elif index == 3:
            self.populate_job_location(detail_item, job_crawler_item)
        elif index == 4:
            self.populate_publish_date(detail_item, job_crawler_item)
        else:
            pass

        self.populate_job_country(detail_item, job_crawler_item)

        job_crawler_item['source'] = self.name
        job_crawler_item['crawled_date'] = datetime.datetime.now()


    def populate_job_title(self, detail_item, job_crawler_item):

        job_crawler_item['job_title'] = detail_item.re(r'<a.*>(.*)</a>')[0]
        job_crawler_item['job_details_link'] = 'http://www.sgxin.com/' + detail_item.re(r'<a.*href="(.*)">.*</a>')[0]

    def populate_salary(self, detail_item, job_crawler_item):
        job_crawler_item['salary'] = detail_item.xpath('./text()').extract()[0]

    def populate_employer_name(self, detail_item, job_crawler_item):
        job_crawler_item['employer_name'] = detail_item.xpath('./text()').extract()[0]

    def populate_job_location(self, detail_item, job_crawler_item):
        job_crawler_item['job_location'] = detail_item.xpath('./text()').extract()[0]

    def populate_job_country(self, detail_item, job_crawler_item):
        job_crawler_item['job_country'] = 'Singapore'

    def populate_publish_date(self, detail_item, job_crawler_item):
        job_crawler_item['publish_date'] = detail_item.xpath('./text()').extract()[0]
        # Convert to the datetime format
        job_crawler_item['publish_date'] = datetime.datetime.strptime(
            datetime.datetime.now().strftime('%Y') + '-' + job_crawler_item.get('publish_date'),
            '%Y-%m-%d') if job_crawler_item.get('publish_date', None) is not None else None

    def retrieve_job_details(self, response):
        job_crawler_item = response.meta['item']

        try:
            job_crawler_item['job_desc'] = \
                response.xpath('//blockquote/p').extract()[0][3:-4].replace('<br>', '\n').replace('<br/>', '\n') #to strip the <p></p>

            job_crawler_item['contact'] = response.xpath('//*[@id="content"]/div/div[2]/span[9]/text()').extract()[0]
        except:
            pass

        yield job_crawler_item




