# -*- coding: utf-8 -*-
from flask import Flask, redirect, url_for, make_response
from flask.templating import render_template
from flask import g, request
#import sqlite3 as dbi
import pg8000 as dbi
import config
import json
import os
import xlsxwriter
import unicodecsv
import tempfile
import datetime

from run_housekeeping import run_housekeeping

app = Flask(__name__)

property_names = ['job_title', 'job_desc', 'job_details_link', 'job_location', 'job_country',
                      'salary', 'employer_name', 'publish_date', 'contact', 'source', 'crawled_date']

def connect_db():
    #return dbi.connect(config.DB_FILE)
    return dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)

@app.before_request
def before_request():
    g.db_conn = connect_db()
    #g.db_conn.row_factory = sqlite3.Row

@app.teardown_request
def teardown_request(exception):
    db_conn = getattr(g, 'db_conn', None)
    if db_conn is not None:
        db_conn.close()

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

    page_size = int(page_request.get('size',20)) # convert the string to int
    page_no = int(page_request.get('page_no', 1))

    c = g.db_conn.cursor()
    # rows = c.execute('SELECT * FROM ( \
    #         SELECT * FROM CRAWLED_JOBS ORDER BY publish_date DESC \
    #     ) AS RESULT LIMIT ? OFFSET ?  ', (page_size, page_size*(page_no-1) ) )

    c.execute('SELECT * FROM ( \
            SELECT ' + ','.join(property_names) + ' FROM CRAWLED_JOBS ORDER BY publish_date DESC \
        ) AS RESULT LIMIT %s OFFSET %s  ', (page_size, page_size*(page_no-1) ) )

    rows = c.fetchall()

    paged_result['content'] = [dict(zip(property_names, row)) for row in rows]

    c.execute('SELECT COUNT(*) FROM CRAWLED_JOBS')

    paged_result['total_count'] = c.fetchone()[0]
    
    paged_result['total_pages'] = paged_result['total_count'] / page_size + 1 if paged_result['total_count'] % page_size != 0 else  paged_result['total_count'] / page_size
    
    return json.dumps(paged_result, default=date_handler)

@app.route('/extract/csv')
def extract_to_csv():
    tmp_file = (tempfile.NamedTemporaryFile(prefix='zjobs.', suffix='.csv', delete=False)).name
    c = g.db_conn.cursor()
    c.execute('SELECT ' + ','.join(property_names) + ' FROM CRAWLED_JOBS ORDER BY publish_date DESC')
    rows = c.fetchall()

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

    c = g.db_conn.cursor()
    c.execute('SELECT ' + ','.join(property_names) + ' FROM CRAWLED_JOBS ORDER BY publish_date DESC')
    rows = c.fetchall()


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
    os.system('python run_crawler.py')
    return redirect(url_for('index'))

@app.route('/admin/run_housekeeping', methods=['GET'])
def re_run_housekeeping():
    run_housekeeping()
    return redirect(url_for('index'))

def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.WEB_HTTP_PORT, debug=config.WEB_DEBUG_ENABLED)