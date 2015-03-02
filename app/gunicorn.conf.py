# -*- coding: utf-8 -*-
import os
from os.path import dirname, realpath
import sys

app_home_dir = dirname(dirname(realpath(__file__)))
sys.path.append(app_home_dir)  # setup sys path to use the current app modules

import multiprocessing

from app.context import Config
#bind = '0.0.0.0:8000'
loglevel = 'info'
errorlog = '-'   # to stderr
#errorlog = Config.LOG_FILE
accesslog = '-'   # to stederr
#accesslog = Config.LOG_FILE
# workers = multiprocessing.cpu_count()
workers = 2
# worker_class = 'gevent'
worker_class = 'flask_sockets.worker'
timeout = 60