import pg8000 as dbi
import config
def remove_old_records():
    conn = dbi.connect(host=config.DB_HOST, database=config.DATABASE, user=config.DB_USER, password=config.DB_PASSWORD)
    c = conn.cursor()
    c.execute("DELETE FROM CRAWLED_JOBS WHERE publish_date < NOW() - INTERVAL '" + str(config.HOUSEKEEPING_RECORD_ORDLER_THAN) +" days'")
    conn.commit()
    conn.close()

def run_housekeeping():
    remove_old_records()

if __name__ == '__main__':
    run_housekeeping()
