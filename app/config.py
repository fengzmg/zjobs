# -*- coding: utf-8 -*-
import os

APP_NAME = 'Zjobs'
APP_HOME = '/apps/jobcrawler'
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DATABASE = os.environ.get('DATABASE', 'zjobs')
DB_USER = os.environ.get('DB_USER', 'zjobs')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'zjobs')

FROM_ADDR = 'zorg.groups@gmail.com'

SMTP_HOST = os.environ.get('SMTP_HOST','smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT','587'))
SMTP_USER = os.environ.get('SMTP_USER','zorg.groups@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

WEB_HTTP_PORT = int(os.environ.get('PORT', 33507))
WEB_DEBUG_ENABLED = True

HOUSEKEEPING_RECORD_ORDLER_THAN = 20
EXPORT_TO_FILE_ENABLED = False

APP_HEARTBEAT_URL = 'https://zjobs.herokuapp.com/'



