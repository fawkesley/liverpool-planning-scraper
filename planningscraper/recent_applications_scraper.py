#!/usr/bin/env python

import datetime
import logging
import time

from urllib.parse import urlparse, parse_qs

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import NoSuchElementException


LOG = logging.getLogger(__name__)


class RecentApplicationsScraper():

    ADVANCED_SEARCH_URL = (
        'http://northgate.liverpool.gov.uk/PlanningExplorer17/GeneralSearch.aspx' # noqa
    )
    SEARCH_DATE_TYPE_SELECT = (By.ID, 'cboSelectDateValue')
    SEARCH_DATES_BY_DAYS_RADIO = (By.ID, 'rbDay')
    SEARCH_BETWEEN_DATES = (By.ID, 'rbRange')
    SET_NUMBER_OF_DAYS_SELECT = (By.ID, 'cboDays')
    DATE_RANGE_FROM_INPUT = (By.ID, 'dateStart')
    DATE_RANGE_TO_INPUT = (By.ID, 'dateEnd')

    SEARCH_BUTTON = (By.ID, 'csbtnSearch')

    RESULTS_TABLE = (By.XPATH, "//table[@summary='Results of the Search']")
    NO_RECORDS_FOUND_SPAN = (
        By.XPATH, "//span[contains(text(), 'No Records Found')]"
    )

    NEXT_PAGE_A = (
        By.XPATH,
        "//img[contains(@alt, 'Go to next page')]/parent::a"
    )

    APPLICATION_NUMBER_A = (
        By.XPATH,
        "//td[@title='View Application Details']/a"
    )

    def __init__(self, webdriver):
        self.d = webdriver
        self.wait = WebDriverWait(self.d, 20)

    def get_applications(self):
        for date in self._last_30_days():
            print("Getting applications received {}".format(date))

            self._navigate_to_advanced_search_page()
            # self._search_by_date_received_last_30_days()
            self._search_by_date_received_equal_to(date)
            self._wait_for_results_page()

            for application in self._loop_through_search_result_pages():
                application.update({'received_date': date})
                yield application

    @staticmethod
    def _last_30_days():
        now = datetime.datetime.now()
        for day_offset in range(1, 30):
            yield (now - datetime.timedelta(days=day_offset)).date()

    def _navigate_to_advanced_search_page(self):
        LOG.info('Opening {}'.format(self.ADVANCED_SEARCH_URL))
        self.d.get(self.ADVANCED_SEARCH_URL)

        self.wait.until(
            expected_conditions.visibility_of_element_located(
                self.SEARCH_DATE_TYPE_SELECT
            )
        )

        LOG.info('Found login iframe. Crack on.')

    def _search_by_date_received_last_30_days(self):

        Select(
            self.d.find_element(*self.SEARCH_DATE_TYPE_SELECT)
        ).select_by_visible_text('Date Received')

        self.d.find_element(*self.SEARCH_DATES_BY_DAYS_RADIO).click()

        Select(
            self.d.find_element(*self.SET_NUMBER_OF_DAYS_SELECT)
        ).select_by_visible_text('30')

        self.d.find_element(*self.SEARCH_BUTTON).click()

    def _search_by_date_received_equal_to(self, date):
        assert isinstance(date, datetime.date)
        date_text = date.isoformat()

        Select(
            self.d.find_element(*self.SEARCH_DATE_TYPE_SELECT)
        ).select_by_visible_text('Date Received')

        self.d.find_element(*self.SEARCH_BETWEEN_DATES).click()

        self.d.find_element(*self.DATE_RANGE_FROM_INPUT).send_keys(date_text)
        self.d.find_element(*self.DATE_RANGE_TO_INPUT).send_keys(date_text)

        self.d.find_element(*self.SEARCH_BUTTON).click()

    def _wait_for_results_page(self):
        def find_results_table_or_no_results(d):
            return (
                d.find_elements(*self.RESULTS_TABLE)
                or d.find_elements(*self.NO_RECORDS_FOUND_SPAN)
            )

        self.wait.until(find_results_table_or_no_results)

    def _loop_through_search_result_pages(self):
        while True:
            for td in self.d.find_elements(*self.APPLICATION_NUMBER_A):
                url = td.get_attribute('href')
                northgate_id = self._parse_northgate_id(url)

                yield {
                    'northgate_id': northgate_id,
                    'url': url,
                }

            try:
                self.d.find_element(*self.NEXT_PAGE_A).click()
            except NoSuchElementException:  # no more pages OR "no results"
                break
            else:
                time.sleep(2)  # chill out
                self._wait_for_results_page()

    @staticmethod
    def _parse_northgate_id(url):
        return parse_qs(urlparse(url).query)['PARAM0'][0]
