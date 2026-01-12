import os.path

from base.base import BasePage

from playwright.sync_api import expect


class HomePage(BasePage):
    TITLE_TEXT = "//h1[normalize-space()='Modernize your code']"
    BROWSE_FILES = "//button[normalize-space()='Browse files']"
    SUCCESS_MSG = "//span[contains(text(),'All valid files uploaded successfully!')]"
    TRANSLATE_BTN = "//button[normalize-space()='Start translating']"
    BATCH_HISTORY = "//button[@aria-label='View batch history']"
    CLOSE_BATCH_HISTORY = "//button[@aria-label='Close panel']"
    BATCH_DETAILS = "//div[@class='batch-details']"
    DOWNLOAD_FILES = "//button[normalize-space()='Download all as .zip']"
    RETURN_HOME = "//button[normalize-space()='Return home']"
    SUMMARY = "//span[normalize-space()='Summary']"
    FILE_PROCESSED_MSG = "//span[normalize-space()='3 files processed successfully']"

    def __init__(self, page):
        super().__init__(page)
        self.page = page

    def validate_home_page(self):
        expect(self.page.locator(self.TITLE_TEXT)).to_be_visible()

    def upload_files(self):
        with self.page.expect_file_chooser() as fc_info:
            self.page.locator(self.BROWSE_FILES).click()
            self.page.wait_for_timeout(5000)
            self.page.wait_for_load_state("networkidle")
        file_chooser = fc_info.value
        current_working_dir = os.getcwd()
        file_path1 = os.path.join(current_working_dir, "testdata/q1_informix.sql")
        file_path2 = os.path.join(current_working_dir, "testdata/f1.sql")
        file_path3 = os.path.join(current_working_dir, "testdata/f2.sql")
        file_chooser.set_files([file_path1, file_path2, file_path3])
        self.page.wait_for_timeout(10000)
        self.page.wait_for_load_state("networkidle")
        expect(self.page.locator(self.SUCCESS_MSG)).to_be_visible()

    def upload_unsupported_files(self):
        with self.page.expect_file_chooser() as fc_info:
            self.page.locator(self.BROWSE_FILES).click()
            self.page.wait_for_timeout(5000)
            self.page.wait_for_load_state("networkidle")
        file_chooser = fc_info.value
        current_working_dir = os.getcwd()
        file_path = os.path.join(current_working_dir, "testdata/invalid.py")
        file_chooser.set_files([file_path])
        self.page.wait_for_timeout(4000)
        self.page.wait_for_load_state("networkidle")
        expect(self.page.locator(self.TRANSLATE_BTN)).to_be_disabled()

    def validate_translate(self):
        self.page.locator(self.TRANSLATE_BTN).click()
        expect(self.page.locator(self.DOWNLOAD_FILES)).to_be_enabled(timeout=200000)
        self.page.locator(self.SUMMARY).nth(1).click()
        expect(self.page.locator(self.FILE_PROCESSED_MSG)).to_be_visible()
        self.page.wait_for_timeout(3000)

    def validate_batch_history(self):
        self.page.locator(self.BATCH_HISTORY).click()
        self.page.wait_for_timeout(3000)
        batch_details = self.page.locator(self.BATCH_DETAILS)
        for i in range(batch_details.count()):
            expect(batch_details.nth(i)).to_be_visible()
        self.page.locator(self.CLOSE_BATCH_HISTORY).click()

    def validate_download_files(self):
        self.page.locator(self.DOWNLOAD_FILES).click()
        self.page.wait_for_timeout(7000)
        self.page.locator(self.RETURN_HOME).click()
        self.page.wait_for_timeout(3000)
        expect(self.page.locator(self.TITLE_TEXT)).to_be_visible()
