#!/usr/bin/env python

import time
import os
import stat
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
from .db import applications

LOG = None

RECENT_CSV = pjoin(dirname(__file__), '..', '_cache', 'recent_urls.csv')


def main(argv):
    configure_logging()
    if recent_applications_needs_updating():
        find_recent_applications()

    for row in get_applications_needing_scraping():
        row.update(scrape_single_application(row['url']))

        try:
            applications.upsert(row, 'northgate_id')
        except:
            pprint(row)
            raise

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

    return (today - most_recent['received_date']).days > 2


def file_age_in_seconds(pathname):
    return time.time() - os.stat(pathname)[stat.ST_MTIME]


def get_applications_needing_scraping():
    # Keep coming back to applications according to the schedule:
    #
    # brand new applications
    # received 0-90 days: every day
    # received 91-365 days: every week
    # received 365+ days: every month
    #
    # - extract_datetime = NULL
    # - extract_datetime older than 1 day AND received_date < 90 days
    #
    # Then we will keep refreshing applications as they progress

    return applications.find(extract_datetime=None, order_by='northgate_id')


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
