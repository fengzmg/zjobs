# -*- coding: utf-8 -*-
import os
APP_HOME = '/apps/jobcrawler'
#DB_FILE = APP_HOME + '/db/jobcrawler.db'
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DATABASE = os.environ.get('DATABASE', 'zjobs')
DB_USER = os.environ.get('DB_USER', 'zjobs')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'zjobs')

SEND_EMAIL_ENABLED = False
IS_CLEAN_INSTALL = True  # used in create_db.py 
REFRESH_DB_ENABLED = False

TO_ADDRS = ['mengfeng0904@gmail.com', 'cathytheone@live.cn']
FROM_ADDR = 'zorg.groups@gmail.com'
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'zorg.groups@gmail.com'
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

JOB_RULE_OUT_PATTERN = u'找*工作|找*[工|活|职]|求职|换[工|公]*|本人|承接|我人'
AGENT_RULE_OUT_PATTERN = u'中介|签证|经纪|劳务|补习|服务|房|[交|找]*友|有缘|门票|派单|批发|活动|护发|加盟|诚收|特惠|你想*|微商|社交|课程|咨询|代购|大牌\d+|便宜|免费|情人|歌手|夜场|投资|注册|网络|旅游'

WEB_HTTP_PORT = int(os.environ.get('PORT', 33507))
WEB_DEBUG_ENABLED = True

HOUSEKEEPING_RECORD_ORDLER_THAN = '7 days'
EXPORT_TO_FILE_ENABLED = False