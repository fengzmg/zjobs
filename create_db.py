#import sqlite3  #uncomment this when using sqlite3
import pg8000  as dbi# comment this when using sqlite3
import config

#conn = sqlite3.connect(config.DB_FILE)
conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
#conn = dbi.connect('postgres://zjobs:zjobs@localhost:5432/zjobs')
c = conn.cursor()

if config.IS_CLEAN_INSTALL:
    c.execute('DROP TABLE IF EXISTS CRAWLED_JOBS;')
    c.execute('DROP INDEX IF EXISTS source_job_title_idx;')

# c.execute('''
#     CREATE TABLE IF NOT EXISTS CRAWLED_JOBS(
#         source            text,
#         crawled_date      timestamp,
#         publish_date      timestamp,
#         job_title         text,
#         job_desc          text,
#         job_details_link  text,
#         job_location      text,
#         job_country       text,
#         salary            text,
#         employer_name     text,
#         contact           text
#     );
# ''')

c.execute('''
    CREATE TABLE IF NOT EXISTS CRAWLED_JOBS(
        source            text,
        crawled_date      date,
        publish_date      date,
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
    CREATE UNIQUE INDEX source_job_title_idx ON CRAWLED_JOBS(source, job_title)
''')

conn.commit()
conn.close()