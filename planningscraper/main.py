#!/usr/bin/env python

import time
import os
import stat
import random
import datetime
import io
import logging
import sys

from os.path import dirname, join as pjoin
from pprint import pprint

from seleniumrequests import Firefox
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from .recent_applications_scraper import RecentApplicationsScraper
from .application_scraper import scrape_single_application
from .output import output_data
from .db import applications, db
from .sql import SQL_DAYS_SINCE_RECEIVED, SQL_DAYS_SINCE_SCRAPE

LOG = None

RECENT_CSV = pjoin(dirname(__file__), '..', '_cache', 'recent_urls.csv')


def main(argv):
    random.seed(datetime.date.today().isoformat())
    configure_logging()
    find_new_application_ids()
    get_or_refresh_data_for_applications()
    export_data_to_files()


def find_new_application_ids():
    LOG.info('Step 1: Find brand new application ids/URLs')

    if recent_applications_needs_updating():
        find_recent_applications()
    else:
        LOG.info("We're pretty up to date already.")


def get_or_refresh_data_for_applications():
    LOG.info('Step 2: (Re)visit known applications & update database')

    for row in get_applications_needing_scraping():
        url = row.pop('url')
        northgate_id = row.pop('northgate_id')

        LOG.info('Updating northgate id {}, url {}'.format(northgate_id, url))

        new_row = {
            'northgate_id': northgate_id
        }
        new_row.update(scrape_single_application(url))

        try:
            applications.upsert(new_row, 'northgate_id')
        except:
            pprint(new_row)
            raise


def export_data_to_files():
    LOG.info('Step 3: Export data to CSV/JSON')
    output_data(pjoin(dirname(__file__), '..', '..',
                      'liverpool-planning-data'))


def configure_logging():
    # log to stdout, not the default stderr
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    global LOG
    LOG = logging.getLogger('')


def recent_applications_needs_updating():
    most_recent = applications.find_one(order_by='-received_date')
    if most_recent is None:
        return True

    today = datetime.date.today()

    return (today - most_recent['received_date']).days > 2  # TODO: make it 1


def file_age_in_seconds(pathname):
    return time.time() - os.stat(pathname)[stat.ST_MTIME]


def get_applications_needing_scraping():
    """
    Return applications (database rows) that need re-scraping according to
    a schedule.
    Keep returning to applications, but do it less frequently as they become
    older.
    """

    need_updating = []

    totally_new = list(applications.find(extract_datetime=None))
    zero_to_ninety = find_applications_need_refreshing_0_to_90_days()
    ninety_one_to_365 = find_applications_need_refreshing_91_to_365_days()
    one_year_plus = find_applications_need_refreshing_365_days_plus()

    random.shuffle(totally_new)
    random.shuffle(zero_to_ninety)
    random.shuffle(ninety_one_to_365)
    random.shuffle(one_year_plus)

    need_updating.extend(totally_new)
    need_updating.extend(zero_to_ninety)
    need_updating.extend(ninety_one_to_365)
    need_updating.extend(one_year_plus)

    LOG.info('{} totally new, {} 0-90 days, {} 91-365 days, '
             '{} 365+ days'.format(
                 len(totally_new), len(zero_to_ninety), len(ninety_one_to_365),
                 len(one_year_plus)))

    return need_updating


def find_applications_need_refreshing_0_to_90_days():
    """
    Visit applications received within 90 days every day as this is the
    period where they change the most.
    """

    query = (
        'SELECT * from applications WHERE '
        '    {days_since_scrape} > 0.8 AND '
        '    {days_since_received} < 90'.format(
                days_since_scrape=SQL_DAYS_SINCE_SCRAPE,
                days_since_received=SQL_DAYS_SINCE_RECEIVED
            )
    )

    return list(db.query(query))


def find_applications_need_refreshing_91_to_365_days():
    """
    Visit applications that are 3-12 months old every week as they probably
    aren't changing much.
    """

    query = (
        'SELECT * from applications WHERE '
        '    {days_since_scrape} >= 6.5 AND '
        '    90 <= {days_since_received} AND '
        '    {days_since_received} < 365'.format(
                days_since_scrape=SQL_DAYS_SINCE_SCRAPE,
                days_since_received=SQL_DAYS_SINCE_RECEIVED
            )
    )
    return list(db.query(query))


def find_applications_need_refreshing_365_days_plus():
    """
    Visit 1 year+ old applications once per month
    """

    query = (
        'SELECT * from applications WHERE '
        '    {days_since_scrape} >= 29.5 AND '
        '    365 <= {days_since_received}'.format(
                days_since_scrape=SQL_DAYS_SINCE_SCRAPE,
                days_since_received=SQL_DAYS_SINCE_RECEIVED
            )
    )
    return list(db.query(query))


def find_recent_applications():

    try:
        LOG.info("Starting browser with Webdriver.")
        webdriver = make_webdriver()
    except Exception as e:
        LOG.exception(e)
        raise

    try:
        scraper = RecentApplicationsScraper(webdriver)

    except Exception as e:
        webdriver.quit()
        LOG.exception(e)
        raise

    try:
        for row in scraper.get_applications():
            print('{}'.format(row['northgate_id']))
            applications.upsert(row, ['northgate_id'])

    except Exception as e:
        LOG.exception(e)
        screenshot, html = dump_screenshot_and_source(webdriver)
        raise

    finally:
        webdriver.quit()

    applications_without_data = applications.count(extract_datetime=None)

    LOG.info('There are now {} applications with no data'.format(
        applications_without_data))


def dump_screenshot_and_source(webdriver):
        output_filename = pjoin(
            '/tmp',
            datetime.datetime.now().isoformat()
        )
        screenshot_filename = output_filename + '.png'
        html_filename = output_filename + '.html'

        LOG.warn('Writing html/screenshot to {} and {}'.format(
            html_filename, screenshot_filename))

        webdriver.get_screenshot_as_file(screenshot_filename)

        with io.open(html_filename, 'wb') as f:
            f.write(webdriver.page_source.encode('utf-8'))

        return screenshot_filename, html_filename


def make_webdriver():
    capabilities = DesiredCapabilities.FIREFOX

    # We're pinning to (outdated) Firefox 45.0.2 for now, which doesn't
    # work with the new Marionette/geckodriver stuff - it uses webdriver
    # instead. Disable marionette.
    capabilities["marionette"] = False

    return Firefox(capabilities=capabilities)

if __name__ == '__main__':
    main(sys.argv)
