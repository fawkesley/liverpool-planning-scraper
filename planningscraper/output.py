import datetime
from os.path import join as pjoin

from atomicfile import AtomicFile

from .db import applications
import dataset


def output_data(directory):
    date_earliest, date_latest = get_earliest_latest()

    for date in get_days_between(date_earliest, date_latest):
        output_files_for(date, directory)


def output_files_for(date, directory):
    file_basename = '{}.csv'.format(date.isoformat())
    filename = pjoin(directory, 'applications_received', 'csv', file_basename)

    result = list(applications.find(
        received_date=date,
        order_by='application_number'
    ))

    # TODO: filter unextracted ones

    if len(result) > 0:
        print("Writing {}".format(file_basename))
        with AtomicFile(filename, 'w') as f:
            dataset.freeze(
                result,
                format='csv',
                fileobj=f
            )


def get_earliest_latest():
    earliest = applications.find_one(order_by='received_date')
    latest = applications.find_one(order_by='-received_date')

    if earliest is None or latest is None:
        raise RuntimeError("No data?")

    return earliest['received_date'], latest['received_date']


def get_days_between(earliest, latest):
    for offset in range(0, (latest - earliest).days + 1):
        yield earliest + datetime.timedelta(days=offset)
