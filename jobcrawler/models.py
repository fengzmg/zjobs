# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import datetime
import re
import pg8000

try:
    import simplejson as json
except ImportError:
    import json

from scrapy.item import BaseItem

from app.context import Datasource, logger

from app.context import Config as config


class BaseObject(BaseItem):
    datasource = Datasource.get_instance()
    property_names = []
    key_properties = []
    order_properties = []
    table_name = None

    @classmethod
    def connect_db(self):
        return self.datasource.get_connection()

    @classmethod
    def from_dict(cls, dict_obj):
        new_obj = cls()
        for property_name, property_value in dict_obj.iteritems():
            if hasattr(new_obj, property_name):
                setattr(new_obj, property_name, property_value)
        return new_obj

    @classmethod
    def extract_records_as_bytes(cls, format='txt'):
        import xlsxwriter
        import unicodecsv
        import tempfile
        import os
        tmp_file = (tempfile.NamedTemporaryFile(prefix='zjobs.%s.' % cls.__name__, suffix=('.%s' % format), delete=False)).name
        try:
            records = cls.findall()
            if format.lower() == 'xlsx':
                workbook = xlsxwriter.Workbook(tmp_file, {'default_date_format': 'yyyy-mm-dd'})
                worksheet = workbook.add_worksheet('crawled_jobs')
                worksheet.set_column('A:M', 40)
                worksheet.write_row(0, 0, [property_name.upper() for property_name in cls.property_names])
                for rowIdx, record in enumerate(records):
                    worksheet.write_row(rowIdx + 1, 0, [getattr(record, property_name) for property_name in cls.property_names])
                workbook.close()
            elif format.lower() == 'csv':
                with open(tmp_file, 'w') as f:
                    writer = unicodecsv.writer(f, encoding='utf-8')
                    writer.writerow([property_name.upper() for property_name in cls.property_names])
                    for record in records:
                        writer.writerow([getattr(record, property_name) for property_name in cls.property_names])
            elif format.lower() == 'txt':
                with open(tmp_file, 'w') as f:
                    f.write('\t'.join([property_name.upper() for property_name in cls.property_names]) + '\n')
                    for record in records:
                        f.write('\t'.join([repr(getattr(record, property_name)) if getattr(record, property_name) is not None else ''  for property_name in cls.property_names]) + '\n')
            else:
                raise Exception("'%s' format is not supported" % format)
            file_content = open(tmp_file, 'rb').read()
            return file_content
        except Exception as e:
            logger.error(e)
            logger.error('Unable to extract all records as bytes')
            raise e
        finally:
            os.remove(tmp_file)

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
    def find(cls, criteria_obj=None):
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT ' + ','.join(cls.property_names) + ' FROM ' + cls.table_name + ' WHERE ' + ' AND '.join([ '%s=?' % property  for property in cls.key_properties]),
                      tuple([getattr(criteria_obj, property) for property in cls.key_properties]))
            return cls.from_dict(dict(zip(cls.property_names, c.fetchone())))
        except Exception as e:
            logger.debug(e)
            return None
        finally:
            conn.close()

    def remove(self):
        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('DELETE FROM ' + self.table_name + ' WHERE ' + ' AND '.join(['%s=?' % property for property in self.key_properties]),
                      tuple([getattr(self, property) for property in self.key_properties]))
            conn.commit()
            logger.info('Removed: %s' % self)
        except Exception as e:
            logger.error(e)
            logger.info('Unable to remove: %s' % self)
            conn.rollback()
            raise DatabaseError(str(e))
        finally:
            conn.close()

    def update(self):
        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute(' UPDATE ' + self.table_name +
                      ' SET ' + ', '.join(['%s=?' % property for property in self.property_names]) +
                      ' WHERE ' + ' AND '.join(['%s=?' % property for property in self.key_properties]),
                      tuple([getattr(self, property) for property in self.property_names] + [getattr(self, property) for property in self.key_properties]))
            conn.commit()
            logger.info('Updated: %s' % self)
        except Exception as e:
            logger.error(e)
            logger.info('Unable to update: %s' % self)
            conn.rollback()
            raise DatabaseError(str(e))
        finally:
            conn.close()

    def save(self):
        if self:
            if self.find(self) is None:
                conn = self.connect_db()
                try:
                    c = conn.cursor()
                    c.execute('INSERT INTO ' + self.table_name +
                              '(' +
                              ', '.join(self.property_names) +
                              ') ' +
                              'VALUES (' + ', '.join(['?'] * len(self.property_names)) + ')',
                              tuple([getattr(self, property_name) for property_name in self.property_names])
                              )
                    conn.commit()
                    logger.info('Inserted item: %s' % self)
                except Exception as e:
                    conn.rollback()
                    logger.error('Unable to insert the item: %s' % self)
                    logger.error(e)
                finally:
                    conn.close()
            else:
                self.update()

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
    def find_with_pagination(cls, page_request={'page_no': 1, 'size': 25, 'criteria': None}):
        size = page_request.get('size', 25)
        page_no = page_request.get('page_no', 1)
        criteria = page_request.get('criteria', None)
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            if not criteria:
                c.execute('SELECT * FROM ( \
                        SELECT ' + ','.join(cls.property_names) + ' FROM ' + cls.table_name +
                          ' ORDER BY ' + ', '.join(['%s %s' % (property, order) for (property, order) in cls.order_properties]) +
                        ') AS RESULT LIMIT ? OFFSET ?  ', (size, size * (page_no - 1) ))
            else:
                # TODO need to add the criteria handling
                c.execute('SELECT * FROM ( \
                        SELECT ' + ','.join(cls.property_names) + ' FROM ' + cls.table_name +
                          ' ORDER BY ' + ', '.join(['%s %s' % (property, order) for (property, order) in cls.order_properties]) +
                        ') AS RESULT LIMIT ? OFFSET ?  ', (size, size * (page_no - 1) ))

            return [cls.from_dict(dict(zip(cls.property_names, row))) for row in c.fetchall()]
        finally:
            conn.close()

    def __repr__(self):
        return json.dumps(self, cls=CustomJsonEncoder, sort_keys=True, indent=None, separators=(',', ':'))


class DatabaseError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)

class Document(BaseObject):
    property_names = ['filename', 'content_type', 'content', 'uploaded_by', 'uploaded_date']
    key_properties = ['filename']
    order_properties = [('uploaded_date', 'ASC')]
    table_name = "DOCS"

    def __init__(self, filename=None, content_type=None, content=None, uploaded_by=None, uploaded_date=None):
        self.filename = filename
        self.content_type = content_type
        self.content = content
        self.uploaded_by = uploaded_by
        self.uploaded_date = uploaded_date

    def __repr__(self):
        return "{ filename: %s}" % self.filename


class User(BaseObject):

    property_names = ['username', 'password', 'email', 'subscription_status', 'role', 'last_login_date', 'register_date']
    key_properties = ['username']
    order_properties = [('username', 'ASC')]
    table_name = "USERS"

    def __init__(self, username=None, password=None, email=None, role='standard_user', subscription_status='subscribed'):
        self.username = username
        self.password = password
        self.email = email
        self.role = role
        self.register_date = datetime.datetime.now()
        self.subscription_status = subscription_status
        self.last_login_date = None

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.username)

    def get_role(self):
        return self.role

    @classmethod
    def validate(cls, user=None):
        if user is not None:
            if user.username and user.username != '' and user.password and user.password != '':
                conn = cls.connect_db()
                try:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM " + cls.table_name + " WHERE username=? and password=?", (user.username, user.password))
                    return int(c.fetchone()[0]) > 0
                except Exception as e:
                    logger.error('failed to retrieve the item count')
                    logger.error(e)
                    return False
                finally:
                    conn.close()
            else:
                logger.debug('username or password is empty.. hence returning false in validate()')
                return False
        else:
            return False


class JobItem(BaseObject):

    property_names = ['job_title', 'job_desc', 'job_details_link', 'job_location', 'job_country',
                      'salary', 'employer_name', 'publish_date', 'contact', 'source', 'crawled_date']
    key_properties = ['job_title']
    order_properties = [('publish_date', 'DESC')]
    table_name = 'CRAWLED_JOBS'

    def __init__(self):
        self.job_title = None
        self.job_desc = None
        self.job_details_link = None
        self.job_location = None
        self.job_country = None
        self.salary = None
        self.employer_name = None
        self.publish_date = None  # datetime
        self.crawled_date = None
        self.contact = None
        self.source = None

    @classmethod
    def is_exists(cls, item=None):

        if item:
            job_title = item.job_title
            if job_title:
                conn = cls.connect_db()
                try:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM " + cls.table_name + " WHERE job_title=?", (job_title,))
                    job_item_count = int(c.fetchone()[0])
                    return job_item_count > 0
                except Exception as e:
                    logger.error('failed to retrieve the item count')
                    logger.error(e)
                    return False
                finally:
                    conn.close()
            else:
                logger.debug('item title is None.. hence returning true in is_exist()')
                return True
        else:
            logger.debug('item is None.. hence returning true in is_exist()')
            return True

    @classmethod
    def is_older_required(cls, item=None):
        if item:
            publish_date = item.publish_date
            try:
                if publish_date is None:
                    logger.debug('publish_date is not yet loaded, hence returning true in is_older_required()')
                    return False

                if (datetime.datetime.now() - publish_date).days > int(config.HOUSEKEEPING_RECORD_ORDLER_THAN):
                    return True
            except Exception as e:
                logger.warn('error while calculating the date difference..')
                logger.warn(e)
                return False

            return False
        else:
            logger.debug('item is None.. hence returning true in is_older_required()')
            return True

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
    def remove_blocked_records(cls):
        records = cls.findall()
        count = 0
        for record in records:
            if BlockedContact.is_contact_blocked(record.contact):
                record.remove()
                count += 1
        logger.info('cleared %d job items with blocked contacts' % count)

    @classmethod
    def remove_records_matches_rejection_pattern(cls):
        records = cls.findall()
        count = 0
        for record in records:
            if RejectionPattern.should_be_rejected(record.job_title) or RejectionPattern.should_be_rejected(record.job_desc):
                record.remove()
                count += 1
        logger.info('cleared %d job items matching the rejection pattern' % count)

    def __repr__(self):
        return "{ 'job_title': %s }" % self.job_title


class RejectionPattern(BaseObject):
    property_names = ['reject_pattern', 'reject_reason']
    key_properties = ['reject_pattern']
    order_properties = [('reject_pattern', 'ASC')]
    table_name = 'JOB_REJECTION_RULES'

    def __init__(self, reject_pattern=None, reject_reason=None):
        self.reject_pattern = reject_pattern
        self.reject_reason = reject_reason

    @classmethod
    def should_be_rejected(cls, input_text=''):
        if input_text is None or input_text == '':
            logger.debug('returning False as input_text is None or Empty in should_be_rejected()')
            return False
        try:
            records = cls.findall()
            for record in records:
                match = re.search(record.reject_pattern, input_text)
                if match:
                    logger.debug('returning True as input_text matches %s in should_be_rejected()' % record.reject_pattern)
                    return True
                else:
                    pass
            logger.debug('returning False as input_text does not match any patterns should_be_rejected()')
            return False
        except Exception as e:
            logger.error(e)
            logger.error('returning False as exception occurs in is_contact_blocked()')
            return False


class BlockedContact(BaseObject):
    property_names = ['contact', 'block_reason']
    key_properties = ['contact']
    order_properties = [('contact', 'ASC')]
    table_name = 'BLOCKED_CONTACTS'

    def __init__(self, contact=None, block_reason=None):
        self.contact = contact
        self.block_reason = block_reason

    @classmethod
    def is_contact_blocked(cls, contact=''):
        if contact is None or contact == '':
            logger.debug('returning False as contact is None or Empty in is_contact_blocked()')
            return False
        conn = cls.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM ' + cls.table_name + ' WHERE contact=?', (contact, ))
            return int(c.fetchone()[0]) > 0
        except Exception as e:
            logger.error(e)
            logger.error('returning False as exception occurs in is_contact_blocked()')
            return False
        finally:
            conn.close()


class CustomJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, BaseObject):
            return {key: value for key, value in obj.__dict__.iteritems() if key != 'content'}
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return obj










