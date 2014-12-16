# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import datetime

try:
    import simplejson as json
except ImportError:
    import json

from scrapy.item import BaseItem

from app.config import logger

import pg8000 as dbi
import app.config as config


class BaseObject(BaseItem):
    @classmethod
    def connect_db(cls):
        return dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER,
                           password=config.DB_PASSWORD)

    @classmethod
    def from_dict(cls, dict_obj):
        new_obj = cls()
        for property_name, property_value in dict_obj.iteritems():
            if hasattr(new_obj, property_name):
                setattr(new_obj, property_name, property_value)

        return new_obj


class JobItemDBError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class JobItem(BaseObject):
    job_title = None
    job_desc = None
    job_details_link = None
    job_location = None
    job_country = None
    salary = None
    employer_name = None
    publish_date = None  # datetime
    crawled_date = None
    contact = None
    source = None

    property_names = ['job_title', 'job_desc', 'job_details_link', 'job_location', 'job_country',
                      'salary', 'employer_name', 'publish_date', 'contact', 'source', 'crawled_date']

    table_name = 'CRAWLED_JOBS'

    def __repr__(self):
        return repr(self.__dict__)

    @classmethod
    def save(cls, item=None):
        if item:
            conn = cls.connect_db()
            try:
                c = conn.cursor()

                c.execute('INSERT INTO ' + cls.table_name +
                          '(' +
                          'job_title, job_desc, job_details_link, job_location, job_country,' +
                          'salary, employer_name, publish_date, contact, source, crawled_date' +
                          ') ' +
                          'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                          (
                              item.job_title,
                              item.job_desc,
                              item.job_details_link,
                              item.job_location,
                              item.job_country,
                              item.salary,
                              item.employer_name,
                              item.publish_date,
                              item.contact,
                              item.source,
                              item.crawled_date

                          ))
                logger.info('Saved job: %s' % item.job_title)

                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error('Unable to save the job: %s' % item.job_title)
                logger.error(e)
            finally:
                conn.close()

    @classmethod
    def is_exists(cls, item=None):

        if item:
            job_title = item.job_title

            if job_title:
                conn = cls.connect_db()
                try:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM " + cls.table_name + " WHERE job_title=%s", (job_title,))
                    job_item_count = int(c.fetchone()[0])
                    return job_item_count > 0
                except Exception as e:
                    logger.error('failed to retrieve the item count')
                    logger.error(e)
                    return False
                finally:
                    conn.close()
            else:
                logger.info('item title is None.. hence returning true in is_exist()')
                return True

        else:
            logger.info('item is None.. hence returning true in is_exist()')
            return True

    @classmethod
    def is_older_required(cls, item=None):
        if item:
            publish_date = item.publish_date
            try:
                if publish_date is None:
                    logger.info('publish_date is not yet loaded, hence returning true in is_older_required()')
                    return False

                if (datetime.datetime.now() - publish_date).days > int(config.HOUSEKEEPING_RECORD_ORDLER_THAN):
                    return True
            except Exception as e:
                logger.warn('error while calculating the date difference..')
                logger.warn(e)
                return False

            return False
        else:
            logger.info('item is None.. hence returning true in is_older_required()')
            return True

    @classmethod
    def find_with_pagination(cls, page_request={'page_no': 1, 'size': 25, 'criteria': None}):

        size = page_request.get('size', 25)
        page_no = page_request.get('page_no', 1)
        criteria = page_request.get('criteria', None)

        conn = cls.connect_db()

        try:
            c = conn.cursor()

            if not criteria:

                c.execute('SELECT * FROM ( \
                        SELECT ' + ','.join(cls.property_names) + ' FROM ' + cls.table_name + ' ORDER BY publish_date DESC \
                    ) AS RESULT LIMIT %s OFFSET %s  ', (size, size * (page_no - 1) ))
            else:
                # TODO need to add the criteria handling
                c.execute('SELECT * FROM ( \
                        SELECT ' + ','.join(cls.property_names) + ' FROM ' + cls.table_name + ' ORDER BY publish_date DESC \
                    ) AS RESULT LIMIT %s OFFSET %s  ', (size, size * (page_no - 1) ))

            return [cls.from_dict(dict(zip(cls.property_names, row))) for row in c.fetchall()]
        finally:
            conn.close()

    @classmethod
    def findall(cls):
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            c.execute(
                'SELECT ' + ','.join(cls.property_names) + ' FROM ' + cls.table_name + ' ORDER BY publish_date DESC')
            return [cls.from_dict(dict(zip(cls.property_names, row))) for row in c.fetchall()]
        finally:
            conn.close()

    @classmethod
    def count(cls, criteria=None):

        conn = cls.connect_db()
        try:
            c = conn.cursor()
            if criteria:
                c.execute('SELECT COUNT(*) FROM ' + cls.table_name)
            else:
                c.execute('SELECT COUNT(*) FROM ' + cls.table_name)

            return c.fetchone()[0]
        finally:
            conn.close()

    @classmethod
    def remove_old_records(cls, retention_days=14):
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            c.execute("DELETE FROM " + cls.table_name + " WHERE publish_date < NOW() - INTERVAL '" + str(
                retention_days) + " days'")
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error('Unable to remove the old records')
            logger.error(e)
        finally:
            conn.close()

    @classmethod
    def remove_agent_records(cls):
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            c.execute(
                "DELETE FROM " + cls.table_name + " WHERE contact IN (SELECT contact FROM " + BlockedContact.table_name + ")")
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error('Unable to remove agent records')
            logger.error(e)
        finally:
            conn.close()


class RejectionPattern(BaseObject):
    property_names = ['reject_pattern', 'reject_reason']

    table_name = 'JOB_REJECTION_RULES'

    reject_pattern = None
    reject_reason = None

    def __init__(self, reject_pattern=None, reject_reason=None):
        self.reject_pattern = reject_pattern
        self.reject_reason = reject_reason

    @classmethod
    def findall(cls):
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT ' + ','.join(cls.property_names) + ' FROM ' + cls.table_name + ' ')

            return [cls.from_dict(dict(zip(cls.property_names, row))) for row in c.fetchall()]
        finally:
            conn.close()

    @classmethod
    def find(cls, reject_pattern):
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT ' + ','.join(cls.property_names) + ' FROM ' + cls.table_name + ' WHERE reject_pattern=%s',
                      reject_pattern)
            return cls.property_names, c.fetchone()
        finally:
            conn.close()

    def save(self):
        if self:
            conn = self.connect_db()
            try:
                c = conn.cursor()

                c.execute('INSERT INTO ' + self.table_name +
                          '(' +
                          'reject_pattern, reject_reason' +
                          ') ' +
                          'VALUES (%s, %s)',
                          (
                              self.reject_pattern,
                              self.reject_reason
                          ))
                logger.info('Saved rejection pattern: %s' % self.reject_pattern)

                conn.commit()
            except Exception as e:
                logger.error(e)
                conn.rollback()
                logger.info('Unable to save the rejection pattern: %s' % self.reject_pattern)
                # raise JobItemDBError('Unable to save the job')
            finally:
                conn.close()

    def __repr__(self):
        return json.dumps(self.__dict__)


class BlockedContact(BaseObject):
    property_names = ['contact', 'block_reason']

    table_name = 'BLOCKED_CONTACTS'

    contact = None
    block_reason = None

    def __init__(self, contact=None, block_reason=None):
        self.contact = contact
        self.block_reason = block_reason

    @classmethod
    def findall(cls):
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT ' + ','.join(cls.property_names) + ' FROM ' + cls.table_name + ' ')

            return [cls.from_dict(dict(zip(cls.property_names, row))) for row in c.fetchall()]
        finally:
            conn.close()

    @classmethod
    def find(cls, contact):
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT ' + ','.join(cls.property_names) + ' FROM ' + cls.table_name + ' WHERE contact=%s',
                      contact)
            return cls.from_dict(dict(zip(cls.property_names, c.fetchone()[0])))
        except Exception as e:
            logger.error(e)
            logger.info('returning None as exception occurs in BlockedContact.find()')
            return None
        finally:
            conn.close()

    @classmethod
    def is_contact_blocked(cls, contact):
        if contact is None or contact == '':
            logger.info('returning False as contact is None or Empty in is_contact_blocked()')
            return False
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM ' + cls.table_name + ' WHERE contact=%s', (contact, ))
            return int(c.fetchone()[0]) > 0
        except Exception as e:
            logger.error(e)
            logger.info('returning False as exception occurs in is_contact_blocked()')
            return False
        finally:
            conn.close()

    def remove(self):
        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('DELETE FROM ' + self.table_name + ' WHERE contact=%s', (self.contact, ))
            conn.commit()
            logger.info('Removed blocked contact: ' + self.contact)
        except Exception as e:
            logger.error(e)
            logger.error('Unable to remove blocked contact: ' + self.contact)
            raise JobItemDBError(str(e))
        finally:
            conn.close()

    def save(self):
        if self:
            conn = self.connect_db()
            try:
                c = conn.cursor()

                c.execute('INSERT INTO ' + self.table_name +
                          '(' +
                          'contact, block_reason' +
                          ') ' +
                          'VALUES (%s, %s)',
                          (
                              self.contact, self.block_reason
                          ))

                conn.commit()
                logger.info('Saved BlockedContact: %s' % repr(self))

            except Exception as e:
                logger.error(e)
                conn.rollback()
                logger.info('Unable to save the BlockedContact: %s' % repr(self))
            finally:
                conn.close()

    def __repr__(self):
        return json.dumps(self.__dict__)












