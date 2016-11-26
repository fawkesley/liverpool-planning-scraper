import datetime
from collections import OrderedDict

import requests
import requests_cache

import re

from lxml.html import fromstring
import pytz

UK = pytz.timezone('Europe/London')


def scrape_single_application(url):
    with requests_cache.enabled('cache.db', expire_after=3*3600):
        response = requests.get(url)
    response.raise_for_status()

    return parse_application_page(response.content)


def parse_application_page(page_bytes):
    unicode_html = page_bytes.decode('utf-8')
    root = fromstring(unicode_html)

    return OrderedDict([
       ('extract_datetime', datetime.datetime.now(UK)),
       ('application_number_provisional', parse_application_number_provisional(
           root)
        ),
       ('application_number', parse_application_number(root)),
       ('comments_until_date', parse_comments_until(root)),
       ('committee_date', parse_date_of_committee(root)),
       ('decision', parse_decision(root)),
       ('decision_date', parse_decision_date(root)),
       ('site_address', parse_site_address(root)),
       ('postcode', parse_postcode(root)),
       ('application_type', parse_application_type(root)),
       ('development_type', parse_development_type(root)),
       ('description', parse_description(root)),
       ('current_status', parse_current_status(root)),
       ('applicant', parse_applicant(root)),
       ('agent', parse_agent(root)),
       ('wards', parse_wards(root)),
       ('geo_northing', parse_geo_northing(root)),
       ('geo_easting', parse_geo_easting(root)),
       ('parishes', parse_parishes(root)),
       ('case_officer_name', parse_case_officer_name(root)),
       ('case_officer_number', parse_case_officer_number(root)),
       ('planning_officer_name', parse_planning_officer_name(root)),
       ('determination_level', parse_determination_level(root)),
    ])


def parse_application_number_provisional(lxml_root):
    field = parse_named_field(lxml_root, 'Application Number')

    if is_provisional_application_number(field):
        return field
    else:
        return None


def parse_application_number(lxml_root):
    field = parse_named_field(lxml_root, 'Application Number')
    if not is_provisional_application_number(field):
        return field
    else:
        return None


def is_provisional_application_number(field):
    return field.startswith('PL/INV')


def parse_comments_until(lxml_root):
    text_field = parse_named_field(lxml_root, 'Comments Until')
    if text_field is not None:

        match = re.match('^(?P<date>\d{2}-\d{2}-\d{4}).*', text_field)
        if match:
            return parse_date(match.group('date'))

    return None


def parse_date_of_committee(lxml_root):
    text = parse_named_field(lxml_root, 'Date of Committee')

    if text is not None:
        return parse_date(text)
    else:
        return None


def parse_decision(lxml_root):
    decision_and_date = parse_named_field(lxml_root, 'Decision')
    if not decision_and_date:
        return None

    try:
        return decision_and_date.split('\n')[0].strip()
    except IndexError:
        return None


def parse_decision_date(lxml_root):
    decision_and_date = parse_named_field(lxml_root, 'Decision')
    if not decision_and_date:
        return None

    try:
        date_string = decision_and_date.split('\n')[1].strip()
    except IndexError:
        return None
    else:
        return parse_date(date_string)


def parse_date(date_string):
    """
    '28-02-2016' -> datetime.date(2016, 2, 28)
    """

    match = re.match(
        '^(?P<dd>\d{2})-(?P<mm>\d{2})-(?P<yyyy>\d{4})$', date_string
    )

    if match:
        return datetime.date(
            year=int(match.group('yyyy')),
            month=int(match.group('mm')),
            day=int(match.group('dd'))
        )
    else:
        return None


def parse_application_type(lxml_root):
    return parse_named_field(lxml_root, 'Application Type')


def parse_development_type(lxml_root):
    return parse_named_field(lxml_root, 'Development Type')


def parse_applicant(lxml_root):
    return parse_named_field(lxml_root, 'Applicant')


def parse_agent(lxml_root):
    return parse_named_field(lxml_root, 'Agent')


def parse_case_officer_name(lxml_root):
    """
    Can either be '', a name, or a name + number (separated by newlines)
    """
    name_and_number = parse_named_field(lxml_root, 'Case Officer / Tel')
    if not name_and_number:
        return None

    lines = name_and_number.split('\n')

    try:
        return lines[0].strip()
    except IndexError:
        return None


def parse_case_officer_number(lxml_root):
    name_and_number = parse_named_field(lxml_root, 'Case Officer / Tel')
    if not name_and_number:
        return None

    lines = name_and_number.split('\n')

    try:
        match = re.search('(\d{5,20})', lines[1])
    except IndexError:
        return None
    else:
        if match is not None:
            return match.groups()[0]


def parse_planning_officer_name(lxml_root):
    return parse_named_field(lxml_root, 'Planning Officer')


def parse_determination_level(lxml_root):
    return parse_named_field(lxml_root, 'Determination Level')


def parse_wards(lxml_root):
    return parse_named_field(lxml_root, 'Wards')


def parse_parishes(lxml_root):
    return parse_named_field(lxml_root, 'Parishes')


def parse_geo_northing(lxml_root):
    geo_text = parse_named_field(lxml_root, 'Location Co ordinates')
    match = re.match('.*Northing\s+(\d{6})', geo_text)
    if match:
        return match.groups()[0]
    else:
        return None


def parse_geo_easting(lxml_root):
    geo_text = parse_named_field(lxml_root, 'Location Co ordinates')
    match = re.match('^Easting\s+(\d{6})', geo_text)
    if match:
        return match.groups()[0]
    else:
        return None


def parse_current_status(lxml_root):
    return parse_named_field(lxml_root, 'Current Status')


def parse_description(lxml_root):
    return parse_named_field(lxml_root, 'Proposal')


def get_address_lines(lxml_root):
    one_line = parse_named_field(lxml_root, 'Site Address')
    if one_line is None:
        return None
    else:
        return [line.strip('\r') for line in one_line.split('\n')]


def parse_postcode(lxml_root):
    address_lines = get_address_lines(lxml_root)
    if not address_lines:
        return None

    possible_postcode = address_lines[-1]

    match = re.match('([Ll]\d{1,2}) ?(\d[A-Za-z]{2})', possible_postcode)

    if match is not None:
        return ' '.join(match.groups()).upper()
    else:
        print("NOT A POSTCODE? {}".format(possible_postcode))
        return None


def parse_site_address(lxml_root):
    address_lines = get_address_lines(lxml_root)
    if address_lines:
        return ', '.join(get_address_lines(lxml_root))
    else:
        return None


def parse_named_field(lxml_root, name):
    div = lxml_root.xpath("//span[text()='{}']/parent::div".format(name))[0]
    description = re.sub('^\s*{}'.format(name), '', div.text_content())
    description = re.sub('\s+$', '', description)
    if not len(description):
        return None
    return description
