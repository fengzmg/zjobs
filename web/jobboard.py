from flask import Flask
from flask.templating import render_template
from flask import g, request
import sqlite3
import config
import json

app = Flask(__name__)

def connect_db():
    return sqlite3.connect(config.DB_FILE)

@app.before_request
def before_request():
    g.db_conn = connect_db()
    g.db_conn.row_factory = sqlite3.Row

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

@app.route('/jobs', methods=['POST'])
def get_jobs():
    # Getting the pagination information
    page_request = request.json
    paged_result = {}
    paged_result['page_request'] = page_request

    page_size = int(page_request.get('size',20)) # convert the string to int
    page_no = int(page_request.get('page_no', 1))

    c = g.db_conn.cursor()
    rows = c.execute('SELECT * FROM ( \
            SELECT * FROM CRAWLED_JOBS ORDER BY publish_date DESC \
        ) LIMIT ? OFFSET ?  ', (page_size, page_size*(page_no-1) ) )

    paged_result['content'] = [dict(item) for item in rows]
    
    paged_result['total_count'] = c.execute('SELECT COUNT(*) FROM CRAWLED_JOBS').fetchone()[0]
    
    paged_result['total_pages'] = paged_result['total_count'] / page_size + 1 if paged_result['total_count'] % page_size != 0 else  paged_result['total_count'] / page_size
    
    return json.dumps(paged_result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.WEB_HTTP_PORT, debug=True)