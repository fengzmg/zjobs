from os.path import dirname, realpath
import sys
import os

app_home_dir = dirname(dirname(realpath(__file__)))
sys.path.append(app_home_dir)

import unittest
import app.config as config
from app.run import AppRunner
from jobcrawler.items import JobItem

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
        AppRunner.get_instance().migrate_db()

        print 'Done setting up test db..'

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(test_db_file)
            #pass
        except:
            pass
        print 'tearing down class'

    @classmethod
    def connect_db(cls):
        return cls.datasource.get_connection()

class TestDatabaseInfra(BaseTestCase):

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

def run_all_tests():
    unittest.main()

if __name__ == '__main__':
    run_all_tests()
