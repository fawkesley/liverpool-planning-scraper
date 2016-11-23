import json
import logging
from os.path import abspath, dirname, join as pjoin
import os
from collections import OrderedDict

from atomicfile import AtomicFile
import dataset

from .db import db
from .sql import SQL_DAYS_SINCE_RECEIVED, SQL_DAYS_SINCE_SCRAPE

YEAR_TO_DATE_FILENAME = pjoin('applications', 'year_to_date.{fmt}')
BY_NUMBER_FILENAME = pjoin('applications', 'by-number',
                           '{application_number}.json')


YEAR_TO_DATE_QUERY = (
    'SELECT * from applications WHERE '
    '    {days_since_received} <= 365 '
    'ORDER BY received_date, northgate_id'.format(
            days_since_scrape=SQL_DAYS_SINCE_SCRAPE,
            days_since_received=SQL_DAYS_SINCE_RECEIVED
        )
)

RECENTLY_EXTRACTED_QUERY = (
    'SELECT * from applications WHERE '
    '    {days_since_scrape} <= 7 AND '
    '    application_number NOT NULL '
    'ORDER BY received_date, northgate_id'.format(
            days_since_scrape=SQL_DAYS_SINCE_SCRAPE,
        )
)

LOG = logging.getLogger(__name__)


def output_data(directory):
    output_year_to_date(directory)
    output_by_application_number(directory)


def output_year_to_date(directory):
    for fmt in ['csv', 'json']:
        filename = abspath(
            pjoin(directory, YEAR_TO_DATE_FILENAME).format(fmt=fmt)
        )

        LOG.info("Writing {}".format(filename))

        with AtomicFile(filename, 'w') as f:
            dataset.freeze(db.query(YEAR_TO_DATE_QUERY), format=fmt, fileobj=f)


def output_by_application_number(directory):

    for row in db.query(RECENTLY_EXTRACTED_QUERY):
        filename = abspath(pjoin(directory, BY_NUMBER_FILENAME)).format(
            application_number=row['application_number']
        )

        mkdir_p(dirname(filename))

        LOG.info("Writing {}".format(filename))

        with AtomicFile(filename, 'w') as f:
            json.dump(sort_by_key(row), f, indent=4)


def sort_by_key(dictionary):
    return OrderedDict(sorted(dictionary.items()))


def mkdir_p(directory):
    if os.path.exists(directory):
        return
    os.makedirs(directory)
