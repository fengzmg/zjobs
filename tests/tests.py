from os.path import dirname, realpath
import sys
import os
app_home_dir = dirname(dirname(realpath(__file__)))
sys.path.append(app_home_dir)

import unittest
import app.config as config
from app.run import migrate_db

import sqlite3 as dbi


test_dir = dirname(realpath(__file__))
test_db_file = test_dir + '/' + 'test.db'

class BaseTestCase(unittest.TestCase):
    @classmethod
    def connect_db(cls):
        return dbi.connect(test_db_file)

    def setUp(self):
        print 'setting up instance'

    def tearDown(self):
        print 'tearing down instance'

    @classmethod
    def setUpClass(cls):
        migrate_db()
        print 'migrated db..'

    @classmethod
    def tearDownClass(cls):
        os.remove(test_db_file)
        print 'tearing down class'

class TestDatabaseInfra(BaseTestCase):
    def test_migrate_db(self):
        conn = self.connect_db()
        print 'connected to db'



def run_all_tests():
    unittest.main()

if __name__ == '__main__':
    run_all_tests()
