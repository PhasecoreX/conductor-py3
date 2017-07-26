"""
Test the locomotive
"""

import unittest

from locomotive import Locomotive


class LocomotiveUnitTest(unittest.TestCase):
    """The Locomotive Unit Test"""

    ddavison = "http://ddavison.io/tests/getting-started-with-selenium.htm"
    browsers = ["firefox", "phantomjs"]

    def test_text_area(self):
        """Test text area"""
        for browser in self.browsers:
            with Locomotive(browser, self.ddavison) as driver:
                driver.text("#textArea", "some text")
                driver.validate_text("#textArea", "some text")

    def test_click(self):
        """Test clicking"""
        for browser in self.browsers:
            with Locomotive(browser, self.ddavison) as driver:
                driver.click("#click")
                driver.validate_present("#click.success")

    def test_text_field(self):
        """Test text fields"""
        for browser in self.browsers:
            with Locomotive(browser, self.ddavison) as driver:
                driver.text("#setTextField", "test")
                driver.validate_text("#setTextField", "test")
                driver.validate_text_not("#setTextField", "testify")

    def test_checkbox(self):
        """Test checkboxes"""
        for browser in self.browsers:
            with Locomotive(browser, self.ddavison) as driver:
                driver.check("#checkbox")
                driver.validate_checked("#checkbox")
                driver.uncheck("#checkbox")
                driver.validate_unchecked("#checkbox")

    def test_dropdown_single(self):
        """Test dropdowns with one option"""
        for browser in self.browsers:
            with Locomotive(browser, self.ddavison) as driver:
                driver.select_text("#select", "Third")
                driver.validate_text("#select", "Third")
                driver.select_value("#select", "2")
                driver.validate_text("#select", "Second")
                driver.text("#select", "First")
                driver.validate_text("#select", "First")
                assert driver.select_value("select") == "1"

    def test_frames(self):
        """Test frame switching"""
        for browser in self.browsers:
            with Locomotive(browser, self.ddavison) as driver:
                driver.switch_to_frame("frame")
                driver.validate_present("#frame_content")
                driver.switch_to_default_content()
                driver.validate_not_present("#frame_content")
                driver.switch_to_frame("frame")
                driver.switch_to_frame()

    def test_windows(self):
        """Test window switching"""
        for browser in self.browsers:
            with Locomotive(browser, self.ddavison) as driver:
                driver.click("a[href='http://google.com']")
                driver.switch_to_window("Google")
                driver.validate_present("[name='q']")
                driver.close_window()
                driver.validate_not_present("[name='q']")
                driver.click(("link", "Open a new tab / window"))
                driver.switch_to_window("Google")
                driver.close_window("Google")

    def test_code_coverage(self):
        """Test that covers a bunch of random stuff for code coverage"""
        for browser in self.browsers:
            with Locomotive(browser, self.ddavison) as driver:
                driver.validate_source_contains("selectOptionByValue")
                driver.validate_source_not_contains("jfow9384yutow3487ytwo43")


#     def test_attributes(self):
#         """Test attribute validation"""
#         for browser in self.browsers:
#             with Locomotive(browser, self.ddavison) as driver:
#                 driver.validate_attribute("#click", "class", "^box$")
#                 driver.click("#click")
#                 driver.validate_attribute("#click", "class", ".*success.*")

if __name__ == '__main__':
    unittest.main()
