# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

from app.config import logger
# import sqlite3 as dbi # uncomment if using sqlite3
import pg8000 as dbi
import app.config as config

class JobItemDBError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

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
    crawled_date = scrapy.Field()
    contact = scrapy.Field()
    source = scrapy.Field()

    property_names = ['job_title', 'job_desc', 'job_details_link', 'job_location', 'job_country',
                      'salary', 'employer_name', 'publish_date', 'contact', 'source', 'crawled_date']

    @staticmethod
    def save(item=None):
        if item:
            #conn = dbi.connect(config.DB_FILE)
            conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
            try:
                c = conn.cursor()
                # c.execute('INSERT INTO CRAWLED_JOBS '
                #           '('
                #           'job_title, job_desc, job_details_link, job_location, job_country,'
                #           'salary, employer_name, publish_date, contact, source, crawled_date'
                #           ') '
                #           'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);',
                #           (
                #               item.get('job_title', None),
                #               item.get('job_desc', None),
                #               item.get('job_details_link', None),
                #               item.get('job_location', None),
                #               item.get('job_country', None),
                #               item.get('salary', None),
                #               item.get('employer_name', None),
                #               item.get('publish_date', None),
                #               item.get('contact', None),
                #               spider.name,
                #               datetime.datetime.now()

                #           ))

                c.execute('INSERT INTO CRAWLED_JOBS '
                          '('
                          'job_title, job_desc, job_details_link, job_location, job_country,'
                          'salary, employer_name, publish_date, contact, source, crawled_date'
                          ') '
                          'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);',
                          (
                              item.get('job_title', None),
                              item.get('job_desc', None),
                              item.get('job_details_link', None),
                              item.get('job_location', None),
                              item.get('job_country', None),
                              item.get('salary', None),
                              item.get('employer_name', None),
                              item.get('publish_date', None),
                              item.get('contact', None),
                              item.get('source', None),
                              item.get('crawled_date', None)

                          ))

                conn.commit()
            except:
                conn.rollack()
                logger.info('Unable to save the job: %s' % item.get('job_title', '--'))
                raise JobItemDBError('Unable to save the job')
            finally:
                conn.close()

            logger.info('Saved job: %s' % item.get('job_title', '--'))

    @staticmethod
    def is_exists(item=None):
        
        if item:
            job_title = item.get('job_title', None)

            if job_title:
                conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM CRAWLED_JOBS WHERE job_title='%s'" % job_title)
                job_item_count = int(c.fetchone()[0])
            
                return job_item_count > 0
            else:
                raise JobItemDBError('job_title cannot be Empty in is_exsits() method')
                
        else:
            raise JobItemDBError('item cannot be Empty in is_exsits() method')

    
    @staticmethod
    def find_with_pagination(page_request={'page_no': 1, 'size': 25, 'criteria': None}):

        size = page_request.get('size', 25)
        page_no = page_request.get('page_no', 1)
        criteria = page_request.get('criteria', None)

        conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
        c = conn.cursor()
        # rows = c.execute('SELECT * FROM ( \
        #         SELECT * FROM CRAWLED_JOBS ORDER BY publish_date DESC \
        #     ) AS RESULT LIMIT ? OFFSET ?  ', (page_size, page_size*(page_no-1) ) )

        if not criteria:

            c.execute('SELECT * FROM ( \
                    SELECT ' + ','.join(JobItem.property_names) + ' FROM CRAWLED_JOBS ORDER BY publish_date DESC \
                ) AS RESULT LIMIT %s OFFSET %s  ', (size, size*(page_no-1) ) )
        else:
            #TODO need to add the criteria handling
            c.execute('SELECT * FROM ( \
                    SELECT ' + ','.join(JobItem.property_names) + ' FROM CRAWLED_JOBS ORDER BY publish_date DESC \
                ) AS RESULT LIMIT %s OFFSET %s  ', (size, size*(page_no-1) ) )

        return JobItem.property_names, c.fetchall()

    @staticmethod
    def findall():
        conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
        c = conn.cursor()
        c.execute('SELECT ' + ','.join(JobItem.property_names) + ' FROM CRAWLED_JOBS ORDER BY publish_date DESC')
        return JobItem.property_names, c.fetchall()

    @staticmethod
    def count(criteria=None):
        
        conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
        c = conn.cursor()
        if criteria:
            c.execute('SELECT COUNT(*) FROM CRAWLED_JOBS')
        else:
            c.execute('SELECT COUNT(*) FROM CRAWLED_JOBS')

        return c.fetchone()[0]

    @staticmethod
    def remove_old_records(retention_days=14):
        conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
        try:
            c = conn.cursor()
            c.execute("DELETE FROM CRAWLED_JOBS WHERE publish_date < NOW() - INTERVAL '" + str(retention_days) +" days'")
            conn.commit()
        except:
            conn.rollback()
            logger.error('Unable to run the housekeeper')
        finally:
            conn.close()








