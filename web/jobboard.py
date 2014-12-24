# -*- coding: utf-8 -*-
from flask.globals import current_app

try:
    import simplejson as json
except ImportError:
    import json
import datetime

from flask import Flask, redirect, url_for, make_response, request, _app_ctx_stack
from flask.templating import render_template

from app.context import Scheduler, logger
from app.run import AppRunner
from jobcrawler.models import JobItem, RejectionPattern, BlockedContact, BaseObject


app = Flask(__name__)

# with app.app_context():
#     print current_app.__dict__
#     print _app_ctx_stack.__dict__

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

@app.route('/jobs/extract/<format>')
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

@app.route('/reject_rules/extract/<format>')
def extract_reject_rules_as_file(format='csv'):
    response = make_response(RejectionPattern.extract_records_as_bytes(format))
    response.headers["Content-Disposition"] = "attachment; filename=reject_rules.%s" % format
    return response

@app.route('/reject_rules/import', methods=['POST'])
def import_reject_rules_from_file():
    file = request.files['file_to_upload']
    redirect_url = request.form.get('redirect_url', url_for('index'))
    for record in RejectionPattern.findall():
        record.remove()
    logger.info('Done removing all existing rejection patterns')
    count = 0
    file.readline()  #for the header, ignore
    for line in file.readlines():
        columns = line.decode('utf-8').split(',')
        RejectionPattern(columns[0], columns[1]).save()
        count += 1
    logger.info('Done importing %d rejection rules from %s' % (count, file.filename))
    return redirect(redirect_url)

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
        logger.error(e)
        response = make_response()
        response.status = 'internal error'
        response.status_code = 500
        return response

    return "OK"

@app.route('/blocked_contacts/extract/<format>')
def extract_blocked_contacts_as_file(format='csv'):
    response = make_response(BlockedContact.extract_records_as_bytes(format))
    response.headers["Content-Disposition"] = "attachment; filename=blocked_contacts.%s" % format
    return response

@app.route('/blocked_contacts/import', methods=['POST'])
def import_blocked_contact_from_file():
    file = request.files['file_to_upload']
    redirect_url = request.form.get('redirect_url', url_for('index'))
    for record in BlockedContact.findall():
        record.remove()
    logger.info('Done removing all existing blocked contacts')

    count = 0
    file.readline()  #for the header, ignore
    for line in file.readlines():
        columns = line.decode('utf-8').split(',')
        BlockedContact(columns[0], columns[1]).save()
        count += 1
    logger.info('Done importing %d blocked contacts from %s' % (count, file.filename))
    return redirect(redirect_url)

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
        {'label': 'Download As Excel', 'link': '/jobs/extract/xlsx', 'menu_item_id': 'extract_jobs_xlsx'})

    return json.dumps(menu_items)

class CustomJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, BaseObject):
            return obj.__dict__
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()

        return obj
