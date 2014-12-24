# -*- coding: utf-8 -*-

from os.path import dirname, realpath
import random
import sys
import os
import datetime

app_home_dir = dirname(dirname(realpath(__file__)))
sys.path.append(app_home_dir)

import unittest
import app.config as config
from app.run import AppRunner
from jobcrawler.models import JobItem, BlockedContact, RejectionPattern
#from app.context import  Datasource as TestDatasource
import sqlite3 as dbi


test_dir = dirname(realpath(__file__))
test_db_file = test_dir + '/' + 'test.db'

class TestDatasource:
    instance = None

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = TestDatasource()
        return cls.instance

    @classmethod
    def get_connection(cls):
        conn = dbi.connect(test_db_file)
        return conn

class BaseTestCase(unittest.TestCase):

    datasource = TestDatasource.get_instance()

    @classmethod
    def setUpClass(cls):
        database_file = open(test_db_file, 'w+')
        database_file.close()
        AppRunner.datasource = cls.datasource
        BlockedContact.datasource = cls.datasource
        JobItem.datasource = cls.datasource
        RejectionPattern.datasource = cls.datasource
        AppRunner.get_instance().migrate_db()

        print 'Done setting up test db..'

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(test_db_file)
            print 'cleared test database file'
        except:
            pass

    @classmethod
    def connect_db(cls):
        return cls.datasource.get_connection()

    def clean_db(self):
        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('DELETE FROM ' + JobItem.table_name)
            c.execute('DELETE FROM ' + BlockedContact.table_name)
            c.execute('DELETE FROM ' + RejectionPattern.table_name)
            print 'Cleaned database...'
            conn.commit()
        except:
            pass
        finally:
            conn.close()


class DatabaseInfraTest(BaseTestCase):

    def test_migrate_db(self):
        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM ' + JobItem.table_name)
            self.assertEqual(c.fetchone()[0], 0, 'Count of job items should be 0')
        except:
            pass
        finally:
            conn.close()

class JobItemTest(BaseTestCase):
    def setUp(self):
        self.clean_db()
        self.job_item = JobItem()
        self.job_item.job_title="Test Job"
        self.job_item.employer_name="Test Job Employer"
        # self.job_item.crawled_date = datetime.datetime.now()
        # self.job_item.publish_date = datetime.datetime.strptime('2014-10-31', '%Y-%m-%d')
        self.job_item.job_country = "Singapore"
        self.job_item.job_desc = "This is a test job"
        self.job_item.contact = "88888888"
        self.source = 'unit_test'

    def tearDown(self):
        pass


    def test_save(self):
        self.job_item.save()
        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM ' + JobItem.table_name)
            self.assertEqual(c.fetchone()[0], 1, 'Count of job items should be 1')
        except:
            pass
        finally:
            conn.close()

    def test_find_all(self):
        self.job_item.save()
        another_job_item = JobItem()
        another_job_item.job_title = 'Another Test Job'
        another_job_item.save()

        records = JobItem.findall()
        print 'Job Items', records
        self.assertEqual(2, len(records))

    def test_find_with_pagination(self):
        for i in range(0, 20):
            job_item = JobItem()
            job_item.job_title='job_item_%d' % i
            job_item.save()

        records = JobItem.find_with_pagination(page_request={'page_no':2, 'size': 10})

        print 'Job Items', records
        self.assertEqual(10, len(records))

    def test_is_exists(self):
        self.job_item.save()
        self.assertTrue(JobItem.is_exists(self.job_item), '%s should exist' % self.job_item.job_title)

    def test_remove_blocked_records(self):
        for i in range(0, 20):
            job_item = JobItem()
            job_item.job_title='job_item_%d' % i
            job_item.contact = str(random.randint(90000000, 99999999))
            job_item.save()

            # mark the contact as blocked
            BlockedContact(job_item.contact, 'For Testing').save()

        # run the remove action
        JobItem.remove_blocked_records()

        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM ' + JobItem.table_name)
            self.assertEqual(c.fetchone()[0], 0, 'Count of job items should be 0')
        except:
            pass
        finally:
            conn.close()

    def test_remove_records_matches_rejection_pattern(self):
        for i in range(0, 20):
            job_item = JobItem()
            job_item.job_title='job_item_%d' % i
            job_item.save()

        # mark the title as blocked
        RejectionPattern('item_\d+', 'For Testing').save()

        # run the remove action
        JobItem.remove_records_matches_rejection_pattern()

        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM ' + JobItem.table_name)
            self.assertEqual(c.fetchone()[0], 0, 'Count of job items should be 0')
        except:
            pass
        finally:
            conn.close()

class BlockedContactTest(BaseTestCase):
    def setUp(self):
        self.clean_db()
        self.blocked_contact = BlockedContact('8888888','Just For Testing')

    def tearDown(self):
        pass

    def test_save(self):
        self.blocked_contact.save()
        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM ' + BlockedContact.table_name)
            self.assertEqual(c.fetchone()[0], 1, 'Count of blocked contacts should be 1')
        except:
            pass
        finally:
            conn.close()

    def test_find_all(self):
        self.blocked_contact.save()
        another_blocked_contact = BlockedContact('99999999', 'Just Another Item for testing')
        another_blocked_contact.save()

        records = BlockedContact.findall()
        print 'BlockedContacts', records
        self.assertEqual(2, len(records))

    def test_find(self):
        self.blocked_contact.save()
        result = BlockedContact.find(self.blocked_contact.contact)
        self.assertEqual(self.blocked_contact.contact, result.contact, 'Item found should be the same as saved')


    def test_remove(self):
        self.blocked_contact.save()
        self.blocked_contact.remove()
        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM ' + BlockedContact.table_name)
            self.assertEqual(c.fetchone()[0], 0, 'Count of blocked contacts should be 0 after removing')
        except:
            pass
        finally:
            conn.close()

    def test_is_contact_blocked(self):
        self.blocked_contact.save()
        self.assertTrue(BlockedContact.is_contact_blocked(self.blocked_contact.contact), 'Contact should been blocked')

class RejectionPatternTest(BaseTestCase):
    def setUp(self):
        self.clean_db()
        self.rejection_pattern = RejectionPattern('[1-9]+', 'Just For Testing')

    def tearDown(self):
        pass

    def test_save(self):
        self.rejection_pattern.save()
        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM ' + RejectionPattern.table_name)
            self.assertEqual(c.fetchone()[0], 1, 'Count of rejection_pattern should be 1')
        except:
            pass
        finally:
            conn.close()

    def test_find_all(self):
        self.rejection_pattern.save()
        another_rejection_pattern = RejectionPattern('[a-z]+', 'Just Another Item for testing')
        another_rejection_pattern.save()

        records = RejectionPattern.findall()
        print 'rejection_pattern', records
        self.assertEqual(2, len(records))

    def test_find(self):
        self.rejection_pattern.save()
        result = RejectionPattern.find(self.rejection_pattern.reject_pattern)
        self.assertEqual(self.rejection_pattern.reject_pattern, result.reject_pattern, 'Item found should be the same as saved')

    def test_remove(self):
        self.rejection_pattern.save()
        self.rejection_pattern.remove()
        conn = self.connect_db()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM ' + RejectionPattern.table_name)
            self.assertEqual(c.fetchone()[0], 0, 'Count of rejection_pattern should be 0 after removing')
        except:
            pass
        finally:
            conn.close()

    def test_should_be_rejected(self):
        RejectionPattern('[1-9]+').save()
        self.assertTrue(RejectionPattern.should_be_rejected('9887'), 'input_text should be rejected')
        self.assertFalse(RejectionPattern.should_be_rejected('abcd'), 'input_text should not be rejected')
        RejectionPattern(u'(?<!非)中介').save()
        self.assertTrue(RejectionPattern.should_be_rejected(u'中介'), 'input_text should be rejected')
        self.assertTrue(RejectionPattern.should_be_rejected(u'是中介'), 'input_text should be rejected')
        self.assertFalse(RejectionPattern.should_be_rejected(u'非中介'), 'input_text should not be rejected')

    def test_extract_records_as_bytes(self):
        RejectionPattern('Pattern1', 'testing1').save()
        RejectionPattern('Pattern2').save()
        RejectionPattern('Pattern3', '测试').save()

        print 'Content as txt: ', RejectionPattern.extract_records_as_bytes('txt')
        print 'Content as excel: ', RejectionPattern.extract_records_as_bytes('xlsx')
        print 'Content as csv: ', RejectionPattern.extract_records_as_bytes('csv')

    def test_get_instance_classname(self):
        self.assertEqual('RejectionPatternTest', self.__class__.__name__)

    @classmethod
    def test_get_classname(cls):
        print cls.__name__

def run_all_tests():
    unittest.main(verbosity=3)

if __name__ == '__main__':
    run_all_tests()
