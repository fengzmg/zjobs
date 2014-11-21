# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import json


class JobItem(scrapy.Item):
    # define the fields for your item here like:
    job_title = scrapy.Field()
    job_desc = scrapy.Field()
    job_details_link = scrapy.Field()
    job_location = scrapy.Field()
    job_country = scrapy.Field()
    salary = scrapy.Field()
    employer_name = scrapy.Field()
    publish_date = scrapy.Field()  # datetime
    contact = scrapy.Field()

