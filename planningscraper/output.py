import datetime
import logging
from os.path import join as pjoin

from atomicfile import AtomicFile
import dataset

from .db import db
from .sql import SQL_DAYS_SINCE_RECEIVED, SQL_DAYS_SINCE_SCRAPE

LOG = logging.getLogger(__name__)


def output_data(directory):
    output_year_to_date(directory)


def output_year_to_date(directory):
    query = (
        'SELECT * from applications WHERE '
        '    {days_since_received} <= 365 '
        'ORDER BY received_date, northgate_id'.format(
                days_since_scrape=SQL_DAYS_SINCE_SCRAPE,
                days_since_received=SQL_DAYS_SINCE_RECEIVED
            )
    )

    for fmt in ['csv', 'json']:
        file_basename = 'year_to_date.{}'.format(fmt)
        filename = pjoin(directory, 'applications', file_basename)

        LOG.info("Writing {}".format(file_basename))
        with AtomicFile(filename, 'w') as f:
            dataset.freeze(
                db.query(query),
                format=fmt,
                fileobj=f
            )
