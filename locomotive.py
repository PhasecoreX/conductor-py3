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
import re

from retrying import retry
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        NoSuchFrameException,
                                        NoSuchWindowException,
                                        WebDriverException)


def retry_on_selenium_exceptions(exc):
    """Determines whether the retry exception is a Selenium based one"""
    return isinstance(exc, NoSuchElementException) or isinstance(
        exc, WebDriverException) or isinstance(exc, NoSuchWindowException) or isinstance(
            exc, NoSuchFrameException)


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

    driver = None
    retry_exp_mult = 2
    retry_exp_max = 1000
    retry_stop = 10000

    def __init__(self, browser, url=None, timeout=10):
        """Ceates a new instance of Locomotive, given a browser name
        There are some optional parameters you can pass in:

        url:     Starting URL, so you don't have to manually call .get() afterwards
        timeout: How long (in seconds) you want Locomotive to keep retrying an action
        """
        # pylint: disable=redefined-variable-type
        browser = browser.lower()
        if browser == "chrome":
            self.driver = webdriver.Chrome()
        elif browser == "firefox":
            self.driver = webdriver.Firefox()
        elif browser == "android":
            self.driver = webdriver.Android()
        elif browser == "edge":
            self.driver = webdriver.Edge()
        elif browser == "ie":
            self.driver = webdriver.Ie()
        elif browser == "opera":
            self.driver = webdriver.Opera()
        elif browser == "phantomjs":
            self.driver = webdriver.PhantomJS()
        elif browser == "safari":
            self.driver = webdriver.Safari()
        else:
            raise NotImplementedError("Browser '{0}' not supported! (Yet?)".format(browser))
        self.driver.implicitly_wait(1)
        if url is not None:
            self.get(url)
        self.retry_stop = timeout * 1000

    def __get_element(self, selector, get_multiple=False):
        select_by, select_value = clean_selector(selector)
        # Find elements
        if select_by == "css":
            elements = self.driver.find_elements_by_css_selector(select_value)
        elif select_by == "id":
            elements = self.driver.find_elements_by_id(select_value.strip("#"))
        elif select_by == "name":
            elements = self.driver.find_elements_by_name(select_value)
        elif select_by == "class":
            elements = self.driver.find_elements_by_class_name(select_value)
        elif select_by == "link":
            elements = self.driver.find_elements_by_link_text(select_value)
        elif select_by == "xpath":
            elements = self.driver.find_elements_by_xpath(select_value)
        else:
            raise NotImplementedError("select_by '{0}' not supported! (Yet?)".format(select_by))
        # Return one or all of the elements
        if get_multiple:
            return elements
        elif len(elements) == 0:
            raise NoSuchElementException("No element found matching {0}({1})".format(select_by,
                                                                                     select_value))
        else:
            return elements[0]

    @retry(wait_exponential_multiplier=retry_exp_mult,
           wait_exponential_max=retry_exp_max,
           stop_max_delay=retry_stop,
           retry_on_exception=retry_on_selenium_exceptions)
    def switch_to_window_regex(self, regex):
        """Switch to a window with a url or window title that is matched by regex"""
        pat = re.compile(regex)
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if pat.match(self.driver.title) or pat.match(self.driver.current_url):
                return self
        raise NoSuchWindowException("Could not switch to window with title/url '{0}'".format(regex))

    def switch_to_window(self, text):
        """Switch to a window with a url or title containing certain text"""
        return self.switch_to_window_regex(".*{0}.*".format(text))

    def close_window_regex(self, regex):
        """Close a window with a url or window title that is matched by regex"""
        pat = re.compile(regex)
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if pat.match(self.driver.title) or pat.match(self.driver.current_url):
                self.driver.close()
                if len(self.driver.window_handles) == 1:
                    self.driver.switch_to.window(self.driver.window_handles[0])
                return self
        raise NoSuchWindowException("Could not close window with title/url '{0}'".format(regex))

    def close_window(self, text=None):
        """Close current window, or a window with a url or title containing certain text"""
        if text is None:
            self.driver.close()
            if len(self.driver.window_handles) == 1:
                self.driver.switch_to.window(self.driver.window_handles[0])
            return self
        else:
            return self.close_window_regex(".*{0}.*".format(text))

    @retry(wait_exponential_multiplier=retry_exp_mult,
           wait_exponential_max=retry_exp_max,
           stop_max_delay=retry_stop,
           retry_on_exception=retry_on_selenium_exceptions)
    def switch_to_frame(self, id_or_name_or_index=None):
        """Switches to a frame, based on CSS ID, name, or index"""
        if id_or_name_or_index is None:
            self.switch_to_default_content()
        else:
            self.driver.switch_to.frame(id_or_name_or_index)
        return self

    def switch_to_default_content(self):
        """Switches to the default content/frame"""
        self.driver.switch_to.default_content()
        return self

    def get(self, url):
        """Navigate to a URL"""
        self.driver.get(url)
        return self

    # True/False methods

    def is_checked(self, selector):
        """Returns true if the selected checkbox/radio is checked/selected, false if not"""
        return self.__get_element(selector).is_selected()

    def is_present(self, selector):
        """Returns true if at least one of the defined element is present and selectable"""
        return len(self.__get_element(selector, get_multiple=True)) > 0

    # Validation methods

    def validate_present(self, selector):
        """Validates that a element is selectable"""
        select_by, select_value = clean_selector(selector)
        assert self.is_present(
            selector) is True, "{0}({1}) is not present on page, when it should be".format(
                select_by, select_value)
        return self

    def validate_not_present(self, selector):
        """Validates that a element is not selectable"""
        select_by, select_value = clean_selector(selector)
        assert self.is_present(
            selector) is False, "{0}({1}) is present on page, when it should not be".format(
                select_by, select_value)
        return self

    def validate_text(self, selector, text):
        """Validates an elements text matches the given text"""
        select_by, select_value = clean_selector(selector)
        actual_text = self.text(selector)
        assert actual_text == text, "{0}({1}) text does not equal '{2}' (actual: '{3}')".format(
            select_by, select_value, text, actual_text)

    def validate_text_not(self, selector, text):
        """Validates an elements text matches the given text"""
        select_by, select_value = clean_selector(selector)
        assert self.text(
            selector) != text, "{0}({1}) text does equal '{2}', when it should not".format(
                select_by, select_value, text)

    def validate_source_contains(self, text):
        """Validates that text is present in the page source"""
        assert text in self.driver.page_source, "{0} is not in page source, when it should be".format(
            text)
        return self

    def validate_source_not_contains(self, text):
        """Validates that text is present in the page source"""
        assert text not in self.driver.page_source, "{0} is in page source, when it should not be".format(
            text)
        return self

    def validate_checked(self, selector):
        """Validates that a checkbox is checked"""
        select_by, select_value = clean_selector(selector)
        assert self.is_checked(selector), "{0}({1}) is not checked, when it should be".format(
            select_by, select_value)
        return self

    def validate_unchecked(self, selector):
        """Validates that a checkbox is checked"""
        select_by, select_value = clean_selector(selector)
        assert not self.is_checked(selector), "{0}({1}) is checked, when it should not be".format(
            select_by, select_value)
        return self

    def alert(self, option, username="", password=""):
        """Clicks an option in an alert"""
        if option in ["ok", "y", "ye", "yes", "accept"]:
            self.driver.switch_to_alert().accept()
        elif option in ["cancel", "n", "no", "dismiss"]:
            self.driver.switch_to_alert().dismiss()
        elif option in ["auth", "a", "user", "password", "pass"]:
            self.driver.switch_to_alert().authenticate(username, password)
        else:
            raise NotImplementedError("Alert option '{0}' not supported! (Yet?)".format(option))
        return self

    @retry(wait_exponential_multiplier=retry_exp_mult,
           wait_exponential_max=retry_exp_max,
           stop_max_delay=retry_stop,
           retry_on_exception=retry_on_selenium_exceptions)
    def text(self, selector, set_value=None):
        """Gets or sets the value/text of an element, selected by CSS
        Optionally, you can pass in a tuple of ("select_by", "value")
        """
        element = self.__get_element(selector)
        if set_value is None:
            if element.tag_name.lower() in ["input", "select", "textarea"]:
                return element.get_attribute("value")
            else:
                return element.text
        else:
            element.clear()
            element.send_keys(set_value)
            return self

    @retry(wait_exponential_multiplier=retry_exp_mult,
           wait_exponential_max=retry_exp_max,
           stop_max_delay=retry_stop,
           retry_on_exception=retry_on_selenium_exceptions)
    def click(self, selector):
        """Clicks an element, selected by CSS
        Optionally, you can pass in a tuple of ("select_by", "value")
        """
        self.__get_element(selector).click()
        return self

    @retry(wait_exponential_multiplier=retry_exp_mult,
           wait_exponential_max=retry_exp_max,
           stop_max_delay=retry_stop,
           retry_on_exception=retry_on_selenium_exceptions)
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

    @retry(wait_exponential_multiplier=retry_exp_mult,
           wait_exponential_max=retry_exp_max,
           stop_max_delay=retry_stop,
           retry_on_exception=retry_on_selenium_exceptions)
    def select(self, select_by, select_by_value, option_type, set_value=None):
        """Gets or sets the option value of a select element"""
        option_type = option_type.lower()
        select_by = select_by.lower()
        if option_type not in ["text", "value"]:
            raise NotImplementedError("Select option_type '{0}' not supported!".format(option_type))

        # Setting and getting are completely different selectors
        if set_value is None:
            element = self.__get_element("css", "select[{0}='{1}']".format(select_by,
                                                                           select_by_value))
            return element.get_attribute(option_type)  # either text or value
        else:
            if option_type == "text":
                element = self.__get_element(
                    "xpath", "//select[@{0}='{1}']/option[normalize-space(.)='{2}']".format(
                        select_by, select_by_value, set_value))

            elif option_type == "value":
                element = self.__get_element("css",
                                             "select[{0}='{1}'] > option[value='{2}']".format(
                                                 select_by, select_by_value, set_value))
            else:
                raise NotImplementedError("Select option_type '{0}' not supported!".format(
                    option_type))
        element.click()
        return self
