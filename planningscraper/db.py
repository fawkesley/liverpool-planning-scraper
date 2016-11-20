from os.path import dirname, join as pjoin

import sqlalchemy

import dataset

db = dataset.connect(
    'sqlite:///{}'.format(pjoin(dirname(__file__), '..', 'db.sqlite'))
)


if __name__ == '__main__':
    applications = db.create_table(
        'applications',
        primary_id='northgate_id',
        primary_type='Integer'
    )

    # We define the columns we want to *force* to a certain type
    applications.create_column('received_date', sqlalchemy.Date)
    applications.create_column('extract_datetime', sqlalchemy.DateTime)
    applications.create_column('application_number_provisional',
                               sqlalchemy.String)
    applications.create_column('application_number', sqlalchemy.String)
    applications.create_column('comments_until_date', sqlalchemy.Date)
    applications.create_column('committee_date', sqlalchemy.Date)
    applications.create_column('decision_date', sqlalchemy.Date)
    applications.create_column('geo_northing', sqlalchemy.Integer)
    applications.create_column('geo_easting', sqlalchemy.Integer)
else:
    applications = db.load_table('applications')
