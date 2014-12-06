# -*- coding: utf-8 -*-
import json
import datetime

from flask import Flask, redirect, url_for, make_response
from flask.templating import render_template
from flask import request

from app.run import run_housekeeper, run_crawler, run_emailer, extract_file_as_bytes, Scheduler
from jobcrawler.items import JobItem, RejectionPattern


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

    size = int(page_request.get('size', 25))  # convert the string to int
    page_no = int(page_request.get('page_no', 1))

    property_names, results = JobItem.find_with_pagination({'page_no': page_no, 'size': size})

    paged_result['content'] = [dict(zip(property_names, row)) for row in results]

    paged_result['total_count'] = JobItem.count()

    paged_result['total_pages'] = paged_result['total_count'] / size + 1 if paged_result['total_count'] / size != 0 else \
        paged_result['total_count'] / size

    return json.dumps(paged_result, default=date_handler)


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
        {'label': 'Download As Excel', 'link': '/extract/xlsx', 'menu_item_id': 'extract_xlsx'})

    return json.dumps(menu_items)


@app.route('/extract/<format>')
def extract_as_file(format='xlsx'):
    response = make_response(extract_file_as_bytes(format))
    response.headers["Content-Disposition"] = "attachment; filename=extracted_jobs_%s.%s" % (
        datetime.datetime.now().strftime('%Y-%m-%d'), format)

    return response


@app.route('/reject_rules', methods=['GET'])
def get_reject_rules():
    reject_rule1 = RejectionPattern('something', 'something')
    reject_rule1.save()

    property_names, results = RejectionPattern.findall()
    records = [dict(zip(property_names, row)) for row in results]
    return json.dumps(records)


@app.route('/admin/run_crawler', methods=['GET'])
def re_run_crawler():
    Scheduler.get_scheduler().add_job(func=run_crawler)
    return redirect(url_for('index'))


@app.route('/admin/run_housekeeper', methods=['GET'])
def re_run_housekeeper():
    Scheduler.get_scheduler().add_job(func=run_housekeeper)
    return redirect(url_for('index'))


@app.route('/admin/run_emailer', methods=['GET'])
def re_run_emailer():
    Scheduler.get_scheduler().add_job(func=run_emailer)
    return redirect(url_for('index'))


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj
