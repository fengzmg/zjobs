# -*- coding: utf-8 -*-
from functools import wraps
import os
from flask.globals import current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import jobcrawler

try:
    import simplejson as json
except ImportError:
    import json
import datetime

from flask import Flask, redirect, url_for, make_response, request, g
from flask.templating import render_template
from werkzeug.routing import BaseConverter

import app as app_context
from app.context import Scheduler, logger
from app.context import Config
from app.run import AppRunner
from jobcrawler.models import JobItem, RejectionPattern, BlockedContact, User, CustomJsonEncoder


app = Flask(__name__)
app.config['SECRET_KEY'] = '1234567890'

class RegexConverter(BaseConverter):
    def __init__(self, map, *items):
        super(RegexConverter, self).__init__(map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


login_manager = LoginManager(app)
login_manager.login_view = 'login'


### decorator for the @roles_required
def roles_required(required_role):
    def wrapper(func):

        @wraps(func)  # use wraps to retain the same function name and docstring
        def decorated_view(*args, **kwargs):
            if current_app.login_manager._login_disabled:
                return func(*args, **kwargs)
            elif not ( current_user.is_authenticated() and current_user.get_role() == required_role):
                return current_app.login_manager.unauthorized()
            return func(*args, **kwargs)
        return decorated_view
    return wrapper


@app.before_request
def before_request():
    g.user = current_user


@app.teardown_request
def teardown_request(exception):
    pass


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/html/<html_file_name>')
def render_html(html_file_name):
    return render_template(html_file_name + '.html')


@app.route('/protected/html/<html_file_name>')
@roles_required('admin')
def render_protected_html(html_file_name):
    return render_template(html_file_name + '.html')


@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')


@login_manager.user_loader
def load_user(id):
    return User.find(User(username=id))


@app.route('/login', methods=['POST'])
def login():
    user_name = request.form.get('username', '')
    user_password = request.form.get('password', '')
    redirect_url = request.form.get('next', url_for('index'))
    if user_name != '' and user_password != '':
        if User.validate(User(user_name, user_password)):
            user = User.find(User(user_name))
            user.last_login_date = datetime.datetime.now()
            user.save()
            login_user(user)
            return redirect(redirect_url)
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/<regex(r"jobs|blocked_contacts"):item_desc>', methods=['GET', 'POST'])
def get_records(item_desc):
    cls = desc_to_cls_mapping.get(item_desc)
    return get_paged_result(request, cls)()


@app.route('/<regex(r"users|reject_rules"):item_desc>', methods=['POST'])
@roles_required('admin')
def get_protected_records(item_desc):
    cls = desc_to_cls_mapping.get(item_desc)
    return get_paged_result(request, cls)()


@app.route('/<item_desc>/save', methods=['POST'])
@roles_required('admin')
def save_records(item_desc):
    cls = desc_to_cls_mapping.get(item_desc)
    cls.from_dict(request.json).save()
    return "OK"


@app.route('/<item_desc>/remove', methods=['POST'])
@roles_required('admin')
def remove_records(item_desc):
    cls = desc_to_cls_mapping.get(item_desc)
    cls.from_dict(request.json).remove()
    return "OK"


@app.route('/<item_desc>/extract/<format>', methods=['GET'])
def extract_records_as_file(item_desc,format):
    cls = desc_to_cls_mapping.get(item_desc)
    response = make_response(cls.extract_records_as_bytes(format))
    response.headers["Content-Disposition"] = "attachment; filename=extracted_%s_%s.%s" % (
        item_desc, datetime.datetime.now().strftime('%Y-%m-%d'), format)
    return response


@app.route('/<item_desc>/import', methods=['POST'])
@roles_required('admin')
def import_records_from_file(item_desc):
    cls = desc_to_cls_mapping.get(item_desc)
    file = request.files['file_to_upload']
    redirect_url = request.form.get('redirect_url', url_for('index'))
    for record in cls.findall():
        record.remove()
    logger.info('Done removing all existing %s' % item_desc)

    count = 0
    file.readline()  #for the header, ignore
    for line in file.readlines():
        columns = line.rstrip('\r\n').rstrip('\n').decode('utf-8').split(',')
        cls(columns[0], columns[1]).save()
        count += 1
    logger.info('Done importing %d %s from %s' % (count, item_desc, file.filename))
    return redirect(redirect_url)



@app.route('/configs', methods=['GET'])
@roles_required('admin')
def get_config():
    return json.dumps(sorted([{'property': key, 'value': value} for (key, value) in Config.__dict__.iteritems() if not key.startswith('__')]),
                      default=lambda o: o.__dict__, sort_keys=True, indent=4)

@app.route('/users/register', methods=['POST'])
def register_user():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    email = request.form.get('email', '')

    if User.find(User(username=username)) is not None:
        response = make_response('internal error - User %s already exists' % username)
        response.status = 'internal error - User %s already exists' % username
        response.status_code = 500
        return response
    else:
        User(username=username, password=password, email=email).save()

    return redirect(url_for('index'))


@app.route('/admin/logs/view/<lines>', methods=['GET'])
@roles_required('admin')
def show_logs(lines='1500'):
    if lines == 'all':
        lines = '10000'  # max to load 10000 records
        output = os.popen('tail -n %d %s' % (int(lines), Config.LOG_FILE)).readlines()[::-1]
    elif lines == 'track':
        cmd = 'awk -v Time="`date -d\'now-5 seconds\' \'+[%Y-%m-%d %H:%M:%S\'`" \'{if($0 > Time) print $0}\' ' +  Config.LOG_FILE
        #print cmd
        output = os.popen(cmd).readlines()[::-1]
    elif lines.isnumeric():
        output = os.popen('tail -n %d %s' % (int(lines), Config.LOG_FILE)).readlines()[::-1]
    return json.dumps(output)

@app.route('/admin/logs/purge', methods=['GET'])
@roles_required('admin')
def purge_logs():
    with open(Config.LOG_FILE, 'w') as f:
        f.write('')
    return redirect('/#/logs')


@app.route('/admin/run', methods=['POST'])
@roles_required('admin')
def run_console_cmd():
    console_cmd = request.json.get('command')
    output_lines = os.popen(console_cmd).read()
    return output_lines


@app.route('/admin/run/<job_name>', methods=['GET'])
@roles_required('admin')
def re_run_job(job_name):
    Scheduler.get_scheduler().add_job(func=getattr(AppRunner.get_instance(),'run_%s' % job_name))
    return redirect(url_for('index'))


@app.route('/menus', methods=['GET'])
def get_menu():
    menu_items = {'menu_items': []}
    if g.user.is_authenticated() and g.user.get_role() == 'admin':
        menu_items['menu_items'].append(
            {'label': 'Run Crawler', 'link': '/admin/run/crawler', 'menu_item_id': 'admin_run_crawler'})
        menu_items['menu_items'].append(
            {'label': 'Run Emailer', 'link': '/admin/run/emailer', 'menu_item_id': 'admin_run_emailer'})
        menu_items['menu_items'].append(
            {'label': 'Run Housekeeper', 'link': '/admin/run/housekeeper', 'menu_item_id': 'admin_run_housekeeper'})
        menu_items['menu_items'].append(
            {'label': 'Config Reject Rules', 'link': '/#/reject_rules', 'menu_item_id': 'admin_config_reject_rules'})
        menu_items['menu_items'].append(
            {'label': 'Config Blocked Contacts', 'link': '/#/blocked_contacts', 'menu_item_id': 'admin_config_blocked_contacts'})
        menu_items['menu_items'].append(
            {'label': 'Config App Setting', 'link': '/#/configs', 'menu_item_id': 'admin_config_app_settings'})
        menu_items['menu_items'].append(
            {'label': 'Manage Users', 'link': '/#/users', 'menu_item_id': 'admin_config_users'})
        menu_items['menu_items'].append(
            {'label': 'View Logs', 'link': '/#/logs', 'menu_item_id': 'admin_view_logs'})
        menu_items['menu_items'].append(
            {'label': 'Command Console', 'link': '/#/console', 'menu_item_id': 'admin_console'})
        menu_items['menu_items'].append(
            {'label': 'View App Dashboard', 'link': 'https://dashboard.heroku.com/apps/zjobs/resources', 'menu_item_id': 'admin_view_app_dashboard'})

    menu_items['menu_items'].append(
        {'label': 'Download As Excel', 'link': '/jobs/extract/xlsx', 'menu_item_id': 'extract_jobs_xlsx'})

    return json.dumps(menu_items)

##############################
# Helper methods
##############################

desc_to_cls_mapping = {
    'jobs' : JobItem,
    'users': User,
    'reject_rules': RejectionPattern,
    'blocked_contacts': BlockedContact
}

def get_paged_result(request, cls):
    def wrapper():
        if request.method == 'POST':
            # Getting the pagination information
            page_request = request.json
            paged_result = {'page_request': page_request}

            size = int(page_request.get('size', 25)) if page_request else 25 # convert the string to int
            page_no = int(page_request.get('page_no', 1)) if page_request else 1

            paged_result['content'] = cls.find_with_pagination({'page_no': page_no, 'size': size})

            paged_result['total_count'] = cls.count()

            paged_result['total_pages'] = paged_result['total_count'] / size + 1 if paged_result['total_count'] % size != 0 else \
                paged_result['total_count'] / size
            return json.dumps(paged_result, cls=CustomJsonEncoder, sort_keys=True, indent=4)
        elif request.method == 'GET':
            return json.dumps(cls.findall(), cls=CustomJsonEncoder, sort_keys=True, indent=4)
    return wrapper