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


class Locomotive(object):
    """The locomotive class"""
    # pylint: disable=too-many-public-methods

    driver = None
    retry_exp_mult = 2
    retry_exp_max = 1000
    retry_stop = 10000

    def __init__(self, browser, url=None, timeout=10):
        """Ceates a new instance of Locomotive, given a browser name"""
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

    def __get_element(self, select_by, select_by_value=None):
        """Gets an element, by a select type"""
        if select_by[:1] == "#":
            select_by_value = select_by.strip("#")
            select_by = "id"
        if select_by_value is None:
            raise TypeError("select_by_value must not be None for non-CSS ID selectors")
        select_by = select_by.lower()
        if select_by == "id":
            return self.driver.find_element_by_id(select_by_value.strip("#"))
        if select_by == "name":
            return self.driver.find_element_by_name(select_by_value)
        if select_by == "link":
            return self.driver.find_element_by_link_text(select_by_value)
        if select_by == "css":
            return self.driver.find_element_by_css_selector(select_by_value)
        if select_by == "xpath":
            return self.driver.find_element_by_xpath(select_by_value)
        raise NotImplementedError("select_by '{0}' not supported! (Yet?)".format(select_by))

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

    @retry(wait_exponential_multiplier=retry_exp_mult,
           wait_exponential_max=retry_exp_max,
           stop_max_delay=retry_stop,
           retry_on_exception=retry_on_selenium_exceptions)
    def text(self, select_by, select_by_value=None, set_value=None):
        """Gets or sets the value of an element
        You can pass a CSS ID (e.g. '#textboxid') in the select_by,
        or you can pass in a select type and value (e.g. 'name', 'textboxname')
        """
        element = self.__get_element(select_by, select_by_value)
        if set_value is None:
            return element.get_attribute("value")
        else:
            element.clear()
            element.send_keys(set_value)
            return self

    @retry(wait_exponential_multiplier=retry_exp_mult,
           wait_exponential_max=retry_exp_max,
           stop_max_delay=retry_stop,
           retry_on_exception=retry_on_selenium_exceptions)
    def click(self, select_by, select_by_value=None):
        """Clicks an element
        You can pass a CSS ID (e.g. '#submitbuttonid') in the select_by,
        or you can pass in a select type and value (e.g. 'name', 'submitbuttonname')
        """
        self.__get_element(select_by, select_by_value).click()
        return self

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

    # Here are more precise helper functions

    # Text
    def text_i(self, css_id, set_text=None):
        """Gets or sets the text/value of an element, selected by CSS ID"""
        return self.text("id", css_id, set_text)

    def text_n(self, css_name, set_text=None):
        """Gets or sets the text/value of an element, selected by CSS name"""
        return self.text("name", css_name, set_text)

    def text_c(self, css_selector, set_text=None):
        """Gets or sets the text/value of an element, selected by custom CSS selector"""
        return self.text("css", css_selector, set_text)

    def text_x(self, xpath_selector, set_text=None):
        """Gets or sets the text/value of an element, selected by custom XPATH selector"""
        return self.text("xpath", xpath_selector, set_text)

    # Click
    def click_i(self, css_id):
        """Clicks an element, selected by CSS ID"""
        return self.click("id", css_id)

    def click_n(self, css_name):
        """Clicks an element, selected by CSS name"""
        return self.click("name", css_name)

    def click_c(self, css_selector):
        """Clicks an element, selected by a custom CSS selector"""
        return self.click("css", css_selector)

    def click_x(self, xpath_selector):
        """Clicks an element, selected by a custom XPATH selector"""
        return self.click("xpath", xpath_selector)

    def click_l(self, link_text):
        """Clicks an element, selected by link text"""
        return self.click("link", link_text)

    # Select Text
    def select_it(self, css_id, set_text=None):
        """Gets or sets the option text of a select element, selected by CSS ID"""
        return self.select("id", css_id, "text", set_text)

    def select_nt(self, css_name, set_text=None):
        """Gets or sets the option text of a select element, selected by name"""
        return self.select("name", css_name, "text", set_text)

    def select_ct(self, css_selector, set_text=None):
        """Gets or sets the option text of a select element, selected by custom CSS selector"""
        return self.select("css", css_selector, "text", set_text)

    def select_xt(self, xpath_selector, set_text=None):
        """Gets or sets the option text of a select element, selected by custom XPATH selector"""
        return self.select("xpath", xpath_selector, "text", set_text)

    # Select Value
    def select_iv(self, css_id, set_value=None):
        """Gets or sets the option value of a select element, selected by CSS ID"""
        return self.select("id", css_id, "value", set_value)

    def select_nv(self, css_name, set_value=None):
        """Gets or sets the option value of a select element, selected by name"""
        return self.select("name", css_name, "value", set_value)

    def select_cv(self, css_selector, set_value=None):
        """Gets or sets the option value of a select element, selected by custom CSS selector"""
        return self.select("css", css_selector, "value", set_value)

    def select_xv(self, xpath_selector, set_value=None):
        """Gets or sets the option value of a select element, selected by custom XPATH selector"""
        return self.select("xpath", xpath_selector, "value", set_value)
