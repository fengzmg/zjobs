import sqlite3
import config

conn = sqlite3.connect(config.DB_FILE)
c = conn.cursor()

if config.IS_CLEAN_INSTALL:
    c.execute('DROP TABLE IF EXISTS CRAWLED_JOBS;')
    c.execute('DROP INDEX IF EXISTS source_job_title_idx;')

c.execute('''
    CREATE TABLE IF NOT EXISTS CRAWLED_JOBS(
        source            text,
        crawled_date      timestamp,
        publish_date      timestamp,
        job_title         text,
        job_desc          text,
        job_details_link  text,
        job_location      text,
        job_country       text,
        salary            text,
        employer_name     text,
        contact           text
    );
''')

c.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS source_job_title_idx ON CRAWLED_JOBS(source, job_title)
''')

conn.commit()
conn.close()