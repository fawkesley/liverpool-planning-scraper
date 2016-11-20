SQL_DAYS_SINCE_SCRAPE = "julianday('now')-julianday(extract_datetime)"
SQL_DAYS_SINCE_RECEIVED = "julianday('now')-julianday(received_date)"
