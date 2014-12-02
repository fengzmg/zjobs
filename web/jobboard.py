# -*- coding: utf-8 -*-
from flask import Flask, redirect, url_for, make_response
from flask.templating import render_template
from flask import g, request
import app.config as config
import json
import os
import xlsxwriter
import unicodecsv
import tempfile
import datetime

from app.run import run_housekeeper, run_crawler

from jobcrawler.items import JobItem


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

@app.route('/jobs', methods=['GET','POST'])
def get_jobs():
    # Getting the pagination information
    page_request = request.json
    paged_result = {}
    paged_result['page_request'] = page_request

    size = int(page_request.get('size',25)) # convert the string to int
    page_no = int(page_request.get('page_no', 1))

    property_names, results = JobItem.find_with_pagination({'page_no':page_no, 'size':size})

    paged_result['content'] = [dict(zip(property_names, row)) for row in results]

    paged_result['total_count'] = JobItem.count()
    
    paged_result['total_pages'] = paged_result['total_count'] / size + 1 if paged_result['total_count'] / size != 0 else  paged_result['total_count'] / size
    
    return json.dumps(paged_result, default=date_handler)

@app.route('/extract/csv')
def extract_to_csv():
    tmp_file = (tempfile.NamedTemporaryFile(prefix='zjobs.', suffix='.csv', delete=False)).name
    property_names, rows = JobItem.findall()

    with open(tmp_file, 'w') as f:
        writer = unicodecsv.writer(f, encoding='utf-8')
        writer.writerow([property_name.upper() for property_name in property_names])
        for row in rows:
            writer.writerow(row)
        response = make_response(open(tmp_file, 'rb').read())
        response.headers["Content-Disposition"] = "attachment; filename=extracted_jobs_%s.csv" % datetime.datetime.now().strftime('%Y-%m-%d')
    
    os.remove(tmp_file)
    return response

@app.route('/extract/xlsx')
def extract_to_xlsx():
    tmp_file = (tempfile.NamedTemporaryFile(prefix='zjobs.', suffix='.xlsx', delete=False)).name  
    
    property_names, rows = JobItem.findall()
    
    workbook = xlsxwriter.Workbook(tmp_file, {'default_date_format':'yyyy-mm-dd'})
    worksheet = workbook.add_worksheet('crawled_jobs')
    worksheet.set_column('A:M', 40)

    worksheet.write_row(0, 0, [property_name.upper() for property_name in property_names])

    for rowIdx, row in enumerate(rows):
        worksheet.write_row(rowIdx+1, 0, row)
    
    workbook.close()

    response = make_response(open(tmp_file, 'rb').read())
    response.headers["Content-Disposition"] = "attachment; filename=extracted_jobs_%s.xlsx" % datetime.datetime.now().strftime('%Y-%m-%d')
    os.remove(tmp_file)
    return response


@app.route('/admin/run_crawler', methods=['GET'])
def re_run_crawler():
    run_crawler()
    return redirect(url_for('index'))

@app.route('/admin/run_housekeeper', methods=['GET'])
def re_run_housekeeping():
    run_housekeeper()
    return redirect(url_for('index'))

def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.WEB_HTTP_PORT, debug=config.WEB_DEBUG_ENABLED)