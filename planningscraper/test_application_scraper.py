import datetime
import glob
import io

from collections import OrderedDict
from os.path import basename, dirname, join as pjoin

from nose.tools import assert_equal
from application_scraper import parse_application_page

assert_equal.__self__.maxDiff = None


FAKE_NOW = '2016-01-28T16:30:25.000Z'

EXPECTED = {
    '001.html': OrderedDict([
       ('application_number_provisional', 'PL/INV/3482/16'),
       ('application_number', None),
       ('comments_until_date', None),
       ('committee_date', None),
       ('decision', None),
       ('decision_date', None),
       ('site_address', '461 Smithdown Road, Wavertree, LIVERPOOL, L15 3JL'),
       ('postcode', 'L15 3JL'),
       ('application_type', 'Full Planning Permission'),
       ('development_type', None),
       ('description', 'Change of use from a small Builders Merchant (A1) to a Public house with food offer and Nano Brewery (A3/A4) with rentable space for cultural events, film screenings, etc...'),
       ('current_status', 'On-line'),
       ('applicant', 'Mr Andrew James'),
       ('agent', None),
       ('wards', None),
       ('geo_northing', None),
       ('geo_easting', None),
       ('parishes', None),
       ('case_officer_name', None),
       ('case_officer_number', None),
       ('planning_officer_name', None),
       ('determination_level', None),
    ]),
    '002_comments_closed.html': OrderedDict([
       ('application_number_provisional', None),
       ('application_number', '16F/2687'),
       ('comments_until_date', datetime.date(2016, 10, 26)),
       ('committee_date', None),
       ('decision', None),
       ('decision_date', None),
       ('site_address', "McDonald's Restaurant, Hunts Cross Shopping Park, Liverpool, L24 9GB"),  # noqa
       ('postcode', 'L24 9GB'),
       ('application_type', 'Full Planning Permission'),
       ('development_type', 'alterations to building'),
       ('description', 'To install new sliding door entrance'),
       ('current_status', 'REGISTERED'),
       ('applicant', "McDonald's Restaurant"),
       ('agent', None),
       ('wards', 'Allerton and Hunts Cross'),
       ('geo_northing', 384865),
       ('geo_easting', 342314),
       ('parishes', 'City South'),
       ('case_officer_name', 'Jon Woodward'),
       ('case_officer_number', '01512333021'),
       ('planning_officer_name', 'Jon Woodward'),
       ('determination_level', None),
    ]),
    '003_comments_open.html': OrderedDict([
       ('application_number_provisional', None),
       ('application_number', '16H/2670'),
       ('comments_until_date', datetime.date(2016, 12, 8)),
       ('committee_date', None),
       ('decision', None),
       ('decision_date', None),
       ('site_address', "Woolton Wood Lodge, 7B High Street, Liverpool, L25 7TD"),  # noqa
       ('postcode', 'L25 7TD'),
       ('application_type', 'Household'),
       ('development_type', 'extension/addition: 1-storey'),
       ('description', 'To erect single storey extension at the read, garden store, terrace and patio'),
       ('current_status', 'REGISTERED'),
       ('applicant', "Mr & Mrs Andrew Chittenden"),
       ('agent', None),
       ('wards', 'Woolton'),
       ('geo_northing', 386592),
       ('geo_easting', 342208),
       ('parishes', 'City South'),
       ('case_officer_name', 'Caroline Maher'),
       ('case_officer_number', '01512333021'),
       ('planning_officer_name', 'Caroline Maher'),
       ('determination_level', None),
    ]),
}


SAMPLE_DIR = pjoin(dirname(__file__), 'sample_data', 'application_pages')


def test_parse_application_pages():
    for filename in glob.glob(SAMPLE_DIR + '/*.html'):
        yield _test_parse_application_page, basename(filename)


def _test_parse_application_page(filename):
    with io.open(pjoin(SAMPLE_DIR, filename), 'rb') as f:
        parsed = parse_application_page(f.read())
        parsed.pop('extract_datetime')  # TODO: refactor

    expected = EXPECTED[filename]
    assert_equal(expected.keys(), parsed.keys())

    for key, expected_value in expected.items():
        assert_equal(expected_value, parsed[key], key)
