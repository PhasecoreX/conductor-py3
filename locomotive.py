"""
Copyright 2016 Ryan Foster (https://github.com/PhasecoreX)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import math
import re
import time

from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        NoSuchFrameException,
                                        NoSuchWindowException,
                                        WebDriverException)
from selenium.webdriver.support.select import Select


def retry(exceptions, timeout=10, delay=0, tries=10):
    """Retry decorator"""
    if delay < 0:
        raise ValueError("delay must be 0 or greater")
    indefinite = timeout < 0
    tries = math.ceil(tries)

    def decorated(function):
        """Decorated retry function"""

        def wrapper(*args, **kwargs):
            """Retry wrapper"""
            min_tries = tries - 2
            end_time = time.time()
            if not indefinite:
                end_time += timeout
            while True:
                try:
                    return function(*args, **kwargs)
                except exceptions:
                    if delay > 0:
                        time.sleep(delay)
                    if not indefinite and time.time() > end_time and min_tries < 1:
                        break
                if min_tries > 0:
                    min_tries -= 1
            return function(*args, **kwargs)

        return wrapper

    return decorated


def clean_selector(selector):
    """Returns a selector tuple based off of a CSS string"""
    if isinstance(selector, tuple):
        return (selector[0].lower(), selector[1])
    elif isinstance(selector, str):
        return ("css", selector)
    else:
        raise TypeError("selector must be a string or tuple (select_by, select_value)")


class Locomotive(object):
    """The locomotive class"""

    # pylint: disable=too-many-public-methods

    def __init__(self, browser, url=None):
        """Initializes an instance of Locomotive, given a browser name
        You would then use it in a with statement to start the browser
        E.G. 'with Locomotive("firefox") as driver:'

        There are some optional parameters you can pass in:

        url: Starting URL, so you don't have to manually call .get() afterwards
        """
        self._browser = browser.lower()
        self._initial_url = url
        self._driver = None

    def __enter__(self):
        if self._browser == "chrome":
            self._driver = webdriver.Chrome()
        elif self._browser == "firefox":
            self._driver = webdriver.Firefox()
        elif self._browser == "android":
            self._driver = webdriver.Android()
        elif self._browser == "edge":
            self._driver = webdriver.Edge()
        elif self._browser == "ie":
            self._driver = webdriver.Ie()
        elif self._browser == "opera":
            self._driver = webdriver.Opera()
        elif self._browser == "phantomjs":
            self._driver = webdriver.PhantomJS()
        elif self._browser == "safari":
            self._driver = webdriver.Safari()
        else:
            raise NotImplementedError("Browser '{0}' not supported! (Yet?)".format(self._browser))
        # self._driver.implicitly_wait(1)
        if self._initial_url is not None:
            self.get(self._initial_url)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._driver is not None:
            self._driver.quit()

    def __get_element(self, selector, get_multiple=False):
        """Gets a WebElement"""
        select_by, select_value = clean_selector(selector)
        # Find elements
        if select_by == "css":
            elements = self._driver.find_elements_by_css_selector(select_value)
        elif select_by == "id":
            elements = self._driver.find_elements_by_id(select_value.strip("#"))
        elif select_by == "name":
            elements = self._driver.find_elements_by_name(select_value)
        elif select_by == "class":
            elements = self._driver.find_elements_by_class_name(select_value)
        elif select_by == "link":
            elements = self._driver.find_elements_by_link_text(select_value)
        elif select_by == "xpath":
            elements = self._driver.find_elements_by_xpath(select_value)
        else:
            raise NotImplementedError("select_by '{0}' not supported! (Yet?)".format(select_by))
        # Return one or all of the elements
        if get_multiple:
            return elements
        elif not elements:
            raise NoSuchElementException(
                "No element found matching {0}({1})".format(select_by, select_value))
        else:
            return elements[0]

    # Navigation

    def get(self, url):
        """Navigate to a URL"""
        self._driver.get(url)
        return self

    # Page manipulation

    @retry(NoSuchElementException)
    def text(self, selector, set_value=None):
        """Gets or sets the value/text of an element, selected by CSS
        Optionally, you can pass in a tuple of ("select_by", "value")
        """
        return self.__text(selector, set_value)

    def __text(self, selector, set_value=None):
        element = self.__get_element(selector)
        # Get text
        if set_value is None:
            if element.tag_name.lower() in ["input", "textarea"]:
                return element.get_attribute("value")
            elif element.tag_name.lower() == "select":
                return self.__select_text(selector)
            return element.text
        # Set select text
        if element.tag_name.lower() == "select":
            return self.__select_text(selector, set_value)
        # Else just type
        element.clear()
        element.send_keys(set_value)
        return self

    @retry((NoSuchElementException, WebDriverException))
    def click(self, selector):
        """Clicks an element, selected by CSS
        Optionally, you can pass in a tuple of ("select_by", "value")
        """
        self.__get_element(selector).click()
        return self

    @retry(NoSuchElementException)
    def check(self, selector, mark=True):
        """Checks a checkbox/radio button, selected by CSS
        Optionally, you can pass in a tuple of ("select_by", "value")
        """
        if self.is_checked(selector) is not mark:
            self.click(selector)
        return self

    def uncheck(self, selector):
        """Unchecks a checkbox/radio button, selected by CSS
        Optionally, you can pass in a tuple of ("select_by", "value")
        """
        self.check(selector, False)

    def is_checked(self, selector):
        """Returns true if the selected checkbox/radio is checked/selected, false if not"""
        return self.__get_element(selector).is_selected()

    @retry(NoSuchElementException)
    def select_text(self, selector, set_text=None):
        """Gets or sets the text of a select element, selected by CSS
        Optionally, you can pass in a tuple of ("select_by", "value")
        """
        return self.__select_text(selector, set_text)

    def __select_text(self, selector, set_text=None):
        selector = Select(self.__get_element(selector))
        if set_text is None:
            return selector.first_selected_option.text
        else:
            selector.select_by_visible_text(set_text)
        return self

    @retry(NoSuchElementException)
    def select_value(self, selector, set_value=None):
        """Gets or sets the value of a select element, selected by CSS
        Optionally, you can pass in a tuple of ("select_by", "value")
        """
        return self.__select_value(selector, set_value)

    def __select_value(self, selector, set_value=None):
        selector = Select(self.__get_element(selector))
        if set_value is None:
            return selector.first_selected_option.get_attribute("value")
        else:
            selector.select_by_value(set_value)
        return self

    # Alert boxes

    def alert(self, option, username="", password=""):
        """Clicks an option in an alert"""
        if option in ["ok", "y", "ye", "yes", "accept"]:
            self._driver.switch_to.alert.accept()
        elif option in ["cancel", "n", "no", "dismiss"]:
            self._driver.switch_to.alert.dismiss()
        elif option in ["auth", "a", "user", "password", "pass"]:
            self._driver.switch_to.alert.authenticate(username, password)
        else:
            raise NotImplementedError("Alert option '{0}' not supported! (Yet?)".format(option))
        return self

    # Waiting

    def wait(self, seconds):
        """Pauses the script for a set amount of seconds"""
        time.sleep(seconds)
        return self

    def wait_present(self, selector):
        """Waits until an element is present on the page"""
        while True:
            try:
                self.__get_element(selector)
                return self
            except NoSuchElementException:
                time.sleep(0.25)

    def wait_not_present(self, selector):
        """Waits until an element is not present on the page"""
        while True:
            try:
                self.__get_element(selector)
            except NoSuchElementException:
                return self
            time.sleep(0.25)

    def wait_source(self, source):
        """Waits until a string is present in the page source code"""
        while True:
            if source in self._driver.page_source:
                return self
            else:
                time.sleep(0.25)

    def wait_not_source(self, source):
        """Waits until a string is not present in the page source code"""
        while True:
            if source not in self._driver.page_source:
                return self
            else:
                time.sleep(0.25)

    # Window switching

    @retry(NoSuchWindowException)
    def switch_to_window_regex(self, regex):
        """Switch to a window with a url or window title that is matched by regex"""
        pat = re.compile(regex)
        for handle in self._driver.window_handles:
            self._driver.switch_to.window(handle)
            if pat.match(self._driver.title) or pat.match(self._driver.current_url):
                return self
        raise NoSuchWindowException("Could not switch to window with title/url '{0}'".format(regex))

    def switch_to_window(self, text):
        """Switch to a window with a url or title containing certain text"""
        return self.switch_to_window_regex(".*{0}.*".format(text))

    @retry(NoSuchWindowException)
    def close_window_regex(self, regex):
        """Close a window with a url or window title that is matched by regex"""
        pat = re.compile(regex)
        for handle in self._driver.window_handles:
            self._driver.switch_to.window(handle)
            if pat.match(self._driver.title) or pat.match(self._driver.current_url):
                self._driver.close()
                if len(self._driver.window_handles) == 1:
                    self._driver.switch_to.window(self._driver.window_handles[0])
                return self
        raise NoSuchWindowException("Could not close window with title/url '{0}'".format(regex))

    def close_window(self, text=None):
        """Close current window, or a window with a url or title containing certain text"""
        if text is None:
            self._driver.close()
            if len(self._driver.window_handles) == 1:
                self._driver.switch_to.window(self._driver.window_handles[0])
            return self
        else:
            return self.close_window_regex(".*{0}.*".format(text))

    # Frame switching

    @retry(NoSuchFrameException)
    def switch_to_frame(self, id_or_name_or_index=None):
        """Switches to a frame, based on CSS ID, name, or index"""
        if id_or_name_or_index is None:
            self.switch_to_default_content()
        else:
            self._driver.switch_to.frame(id_or_name_or_index)
        return self

    def switch_to_default_content(self):
        """Switches to the default content/frame"""
        self._driver.switch_to.default_content()
        return self

    # Validation methods

    @retry(AssertionError, timeout=2)
    def validate_present(self, selector):
        """Validates that a element is selectable"""
        select_by, select_value = clean_selector(selector)
        assert self.is_present(
            selector) is True, "{0}({1}) is not present on page, when it should be".format(
                select_by, select_value)
        return self

    @retry(AssertionError, timeout=2)
    def validate_not_present(self, selector):
        """Validates that a element is not selectable"""
        select_by, select_value = clean_selector(selector)
        assert self.is_present(
            selector) is False, "{0}({1}) is present on page, when it should not be".format(
                select_by, select_value)
        return self

    @retry((AssertionError, NoSuchElementException), timeout=2)
    def validate_text(self, selector, text):
        """Validates an elements text matches the given text"""
        select_by, select_value = clean_selector(selector)
        actual_text = self.__text(selector)
        assert actual_text == text, "{0}({1}) text does not equal '{2}' (actual: '{3}')".format(
            select_by, select_value, text, actual_text)

    @retry((AssertionError, NoSuchElementException), timeout=2)
    def validate_text_not(self, selector, text):
        """Validates an elements text matches the given text"""
        select_by, select_value = clean_selector(selector)
        assert self.__text(
            selector) != text, "{0}({1}) text does equal '{2}', when it should not".format(
                select_by, select_value, text)

    @retry(AssertionError, timeout=2)
    def validate_source_contains(self, text):
        """Validates that text is present in the page source"""
        assert text in self._driver.page_source, (
            "{0} is not in page source, when it should be".format(text))
        return self

    @retry(AssertionError, timeout=2)
    def validate_source_not_contains(self, text):
        """Validates that text is not present in the page source"""
        assert text not in self._driver.page_source, (
            "{0} is in page source, when it should not be".format(text))
        return self

    @retry((AssertionError, NoSuchElementException), timeout=2)
    def validate_checked(self, selector):
        """Validates that a checkbox is checked"""
        select_by, select_value = clean_selector(selector)
        assert self.is_checked(selector), "{0}({1}) is not checked, when it should be".format(
            select_by, select_value)
        return self

    @retry((AssertionError, NoSuchElementException), timeout=2)
    def validate_unchecked(self, selector):
        """Validates that a checkbox is not checked"""
        select_by, select_value = clean_selector(selector)
        assert not self.is_checked(selector), "{0}({1}) is checked, when it should not be".format(
            select_by, select_value)
        return self

    # Helper methods

    def is_present(self, selector):
        """Returns true if at least one of the defined element is present and selectable"""
        return self.count_present(selector) > 0

    def count_present(self, selector):
        """Returns the number of elements selected by the selector"""
        return len(self.__get_element(selector, get_multiple=True))
