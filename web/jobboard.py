# -*- coding: utf-8 -*-
try:
    import simplejson as json
except ImportError:
    import json
import datetime

from flask import Flask, redirect, url_for, make_response
from flask.templating import render_template
from flask import request

from app.context import Scheduler
from app.run import AppRunner
from jobcrawler.items import JobItem, RejectionPattern, BlockedContact, BaseObject


app = Flask(__name__)


@app.before_request
def before_request():
    pass


@app.teardown_request
def teardown_request(exception):
    pass


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/<html_file_name>.html')
def render_html(html_file_name):
    return render_template(html_file_name + '.html')


@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')


@app.route('/jobs', methods=['GET', 'POST'])
def get_jobs():
    # Getting the pagination information
    page_request = request.json
    paged_result = {'page_request': page_request}

    size = int(page_request.get('size', 25)) if page_request else 25 # convert the string to int
    page_no = int(page_request.get('page_no', 1)) if page_request else 1

    paged_result['content'] = JobItem.find_with_pagination({'page_no': page_no, 'size': size})

    paged_result['total_count'] = JobItem.count()

    paged_result['total_pages'] = paged_result['total_count'] / size + 1 if paged_result['total_count'] / size != 0 else \
        paged_result['total_count'] / size


    return json.dumps(paged_result, cls=CustomJsonEncoder, sort_keys=True, indent=4)


@app.route('/menus', methods=['GET', 'POST'])
def get_menu():
    menu_items = {'menu_items': []}
    menu_items['menu_items'].append(
        {'label': 'Run Crawler', 'link': '/admin/run_crawler', 'menu_item_id': 'admin_run_crawler'})
    menu_items['menu_items'].append(
        {'label': 'Run Emailer', 'link': '/admin/run_emailer', 'menu_item_id': 'admin_run_emailer'})
    menu_items['menu_items'].append(
        {'label': 'Run Housekeeper', 'link': '/admin/run_housekeeper', 'menu_item_id': 'admin_run_housekeeper'})
    menu_items['menu_items'].append(
        {'label': 'Config Reject Rules', 'link': '/#/reject_rules', 'menu_item_id': 'admin_config_reject_rules'})
    menu_items['menu_items'].append(
        {'label': 'Config Blocked Contacts', 'link': '/#/blocked_contacts', 'menu_item_id': 'admin_config_blocked_contacts'})
    menu_items['menu_items'].append(
        {'label': 'Download As Excel', 'link': '/extract/jobs/xlsx', 'menu_item_id': 'extract_jobs_xlsx'})

    return json.dumps(menu_items)


@app.route('/extract/jobs/<format>')
def extract_jobs_as_file(format='xlsx'):
    response = make_response(JobItem.extract_records_as_bytes(format))
    response.headers["Content-Disposition"] = "attachment; filename=extracted_jobs_%s.%s" % (
        datetime.datetime.now().strftime('%Y-%m-%d'), format)

    return response


@app.route('/reject_rules', methods=['GET', 'POST'])
def get_reject_rules():

    records = RejectionPattern.findall()
    return json.dumps(records, default=lambda o: o.__dict__, sort_keys=True, indent=4)

@app.route('/reject_rules/save', methods=['POST'])
def save_reject_rules():
    reject_pattern = RejectionPattern.from_dict(request.json)
    reject_pattern.save()
    return "OK"

@app.route('/reject_rules/remove', methods=['POST'])
def remove_reject_rules():
    reject_pattern = RejectionPattern.from_dict(request.json)
    reject_pattern.remove()
    return "OK"

@app.route('/extract/reject_rules/<format>')
def extract_reject_rules_as_file(format='csv'):
    response = make_response(RejectionPattern.extract_records_as_bytes(format))
    response.headers["Content-Disposition"] = "attachment; filename=reject_rules.%s" % format
    return response

@app.route('/blocked_contacts', methods=['GET', 'POST'])
def get_blocked_contacts():
    records = BlockedContact.findall()
    return json.dumps(records, default=lambda o: o.__dict__, sort_keys=True, indent=4)

@app.route('/blocked_contacts/save', methods=['POST'])
def save_blocked_contact():
    blocked_contact = BlockedContact.from_dict(request.json)
    blocked_contact.save()
    return "OK"

@app.route('/blocked_contacts/remove', methods=['POST'])
def remove_blocked_contact():
    try:
        blocked_contact = BlockedContact.from_dict(request.json)
        blocked_contact.remove()
    except Exception as e:
        app.logger.error(e)
        response = make_response()
        response.status = 'internal error'
        response.status_code = 500
        return response

    return "OK"

@app.route('/extract/blocked_contacts/<format>')
def extract_blocked_contacts_as_file(format='csv'):
    response = make_response(BlockedContact.extract_records_as_bytes(format))
    response.headers["Content-Disposition"] = "attachment; filename=blocked_contacts.%s" % format
    return response

@app.route('/admin/run_crawler', methods=['GET'])
def re_run_crawler():
    Scheduler.get_scheduler().add_job(func=AppRunner.get_instance().run_crawler)
    return redirect(url_for('index'))


@app.route('/admin/run_housekeeper', methods=['GET'])
def re_run_housekeeper():
    Scheduler.get_scheduler().add_job(func=AppRunner.get_instance().run_housekeeper)
    return redirect(url_for('index'))


@app.route('/admin/run_emailer', methods=['GET'])
def re_run_emailer():
    Scheduler.get_scheduler().add_job(func=AppRunner.get_instance().run_emailer)
    return redirect(url_for('index'))



class CustomJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, BaseObject):
            return obj.__dict__
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()

        return obj
