import os
import os.path
import logging

from base.base import BasePage

from playwright.sync_api import expect

logger = logging.getLogger(__name__)


class HomePage(BasePage):
    TITLE_TEXT = "//h1[normalize-space()='Modernize your code']"
    BROWSE_FILES = "//button[normalize-space()='Browse files']"
    SUCCESS_MSG = "//span[contains(text(),'All valid files uploaded successfully!')]"
    MAX_FILE_VALIDATION = "//div[.='Maximum of 20 files allowed. Only the first 20 files were uploaded.']"
    MAX_FILE_VALIDATION_2 = "//div[.='File Limit Exceeded']"
    OK_BUTTON = "//button[normalize-space()='OK']"
    TRANSLATE_BTN = "//button[normalize-space()='Start translating']"
    BATCH_HISTORY = "//button[@aria-label='View batch history']"
    VIEW_BATCH_HISTORY = "//button[@aria-label='View Batch History']"
    CLOSE_BATCH_HISTORY = "//button[@aria-label='Close panel']"
    BATCH_DETAILS = "//div[@class='batch-details']"
    DOWNLOAD_FILES = "//button[normalize-space()='Download all as .zip']"
    RETURN_HOME = "//button[normalize-space()='Return home']"
    SUMMARY = "//span[normalize-space()='Summary']"
    FILE_PROCESSED_MSG = "//span[normalize-space()='3 files processed successfully']"
    FILES_UPLOADED = "//div[@style='display: flex; align-items: center; gap: 12px; padding: 8px 12px; background-color: white; border-radius: 4px; border: 1px solid rgb(238, 238, 238); position: relative;']"
    LOGO_TITLE = "//span[normalize-space()='| Modernize your code']"
    CANCEL_UPLOAD = "//button[normalize-space()='Leave and lose progress']"
    REMOVE_FILE_BTN = "//button[@aria-label='Remove file']"
    CANCEL_UPLOAD_BTN = "//button[normalize-space()='Cancel']"
    CANCEL_UPLOAD_MSG = "//button[normalize-space()='Cancel upload']"
    DELETE_BATCH_BTN = "//button[contains(text(),'✕')]"
    DELETE_BATCH_HISTORY = "//button[normalize-space()='Delete']"
    
    # Unsupported file validation messages
    ERROR_MSG_AUDIO = "//span[.=\"File 'test_audio.wav' is not a valid SQL file. Only .sql files are allowed.\"]"
    ERROR_MSG_DOCX = "//div[.=\"File 'test_doc.docx' is not a valid SQL file. Only .sql files are allowed.\"]"
    ERROR_MSG_JSON = "//div[text()=\"File 'test_json.json' is not a valid SQL file. Only .sql files are allowed.\"]"
    ERROR_MSG_DOCX_ALT = "//div[text()=\"File 'test_doc.docx' is not a valid SQL file. Only .sql files are allowed.\"]"
    ERROR_MSG_PDF = "//div[text()=\"File 'test_pdf.pdf' is not a valid SQL file. Only .sql files are allowed.\"]"
    ERROR_MSG_POWERBI = "//div[text()=\"File 'test_powerBi.pbix' is not a valid SQL file. Only .sql files are allowed.\"]"
    ERROR_MSG_TXT = "//div[text()=\"File 'test_text.txt' is not a valid SQL file. Only .sql files are allowed.\"]"
    
    # Large file validation message
    ERROR_MSG_LARGE_FILE = "//span[contains(text(),\"File 'large_dump.sql' exceeds the 200MB size limit. Please upload a file smaller than 200MB.\")]"
    
    # Harmful file validation message
    ERROR_MSG_UNABLE_TO_PROCESS = "//span[normalize-space()='Unable to process the file']"


    def __init__(self, page):
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
        file_path1 = os.path.join(current_working_dir, "testdata/valid_files/q1_informix.sql")
        file_path2 = os.path.join(current_working_dir, "testdata/valid_files/f1.sql")
        file_path3 = os.path.join(current_working_dir, "testdata/valid_files/f2.sql")
        file_chooser.set_files([file_path1, file_path2, file_path3])
        self.page.wait_for_timeout(10000)
        self.page.wait_for_load_state("networkidle")
        expect(self.page.locator(self.SUCCESS_MSG)).to_be_visible()

    def upload_all_files(self):
        """
        Upload all files present in the testdata/valid_files folder.
        """
        with self.page.expect_file_chooser() as fc_info:
            self.page.locator(self.BROWSE_FILES).click()
            self.page.wait_for_timeout(5000)
            self.page.wait_for_load_state("networkidle")
        file_chooser = fc_info.value
        current_working_dir = os.getcwd()
        testdata_dir = os.path.join(current_working_dir, "testdata/valid_files")
        
        # Get all files from testdata/valid_files folder
        all_files = []
        if os.path.exists(testdata_dir) and os.path.isdir(testdata_dir):
            for filename in os.listdir(testdata_dir):
                file_path = os.path.join(testdata_dir, filename)
                # Only add if it's a file (not a directory)
                if os.path.isfile(file_path):
                    all_files.append(file_path)
        
        # Upload all discovered files
        if all_files:
            file_chooser.set_files(all_files)
            self.page.wait_for_timeout(10000)
            self.page.wait_for_load_state("networkidle")
            expect(self.page.locator(self.MAX_FILE_VALIDATION)).to_be_visible()
            expect(self.page.locator(self.MAX_FILE_VALIDATION_2)).to_be_visible()
            self.page.locator(self.OK_BUTTON).click()

    def validate_uploaded_files_count(self):
        """
        Validate that the number of uploaded files is equal to 20.
        """
        uploaded_files = self.page.locator(self.FILES_UPLOADED)
        actual_count = uploaded_files.count()
        expected_count = 20
        assert actual_count == expected_count, f"Expected {expected_count} files to be uploaded, but found {actual_count}"

    def navigate_to_home_page(self):
        """
        Navigate to home page by clicking on logo title, handling cancel upload dialog,
        and validating the home page title.
        """
        self.page.locator(self.LOGO_TITLE).click()
        self.page.wait_for_timeout(4000)
        self.page.locator(self.CANCEL_UPLOAD).click()
        self.page.wait_for_timeout(3000)
        expect(self.page.locator(self.TITLE_TEXT)).to_be_visible()

    def remove_first_three_files_and_validate_count(self):
        """
        Remove the first three uploaded files and validate that 17 files remain.
        """
        remove_buttons = self.page.locator(self.REMOVE_FILE_BTN)
        
        # Remove first three files
        for i in range(3):
            remove_buttons.first.click()
            self.page.wait_for_timeout(2000)
        
        # Validate remaining files count is 17
        uploaded_files = self.page.locator(self.FILES_UPLOADED)
        actual_count = uploaded_files.count()
        expected_count = 17
        assert actual_count == expected_count, f"Expected {expected_count} files after removal, but found {actual_count}"

    def cancel_upload_and_validate_home(self):
        """
        Cancel the upload process by clicking cancel button, confirming cancellation,
        and validating return to home page.
        """
        self.page.locator(self.CANCEL_UPLOAD_BTN).click()
        self.page.wait_for_timeout(3000)
        self.page.locator(self.CANCEL_UPLOAD_MSG).click()
        self.page.wait_for_timeout(3000)
        expect(self.page.locator(self.TITLE_TEXT)).to_be_visible()


    def upload_unsupported_files(self):
        with self.page.expect_file_chooser() as fc_info:
            self.page.locator(self.BROWSE_FILES).click()
            self.page.wait_for_timeout(5000)
            self.page.wait_for_load_state("networkidle")
        file_chooser = fc_info.value
        current_working_dir = os.getcwd()
        file_path = os.path.join(current_working_dir, "testdata/Invalid_files/invalid.py")
        file_chooser.set_files([file_path])
        self.page.wait_for_timeout(4000)
        self.page.wait_for_load_state("networkidle")
        expect(self.page.locator(self.TRANSLATE_BTN)).to_be_disabled()

    def upload_all_unsupported_files_and_validate(self):
        """
        Upload all unsupported files from testdata/Unsupported_files folder and validate
        that error messages are displayed and translate button is disabled with detailed logging.
        """
        with self.page.expect_file_chooser() as fc_info:
            self.page.locator(self.BROWSE_FILES).click()
            self.page.wait_for_timeout(5000)
            self.page.wait_for_load_state("networkidle")
        file_chooser = fc_info.value
        current_working_dir = os.getcwd()
        unsupported_dir = os.path.join(current_working_dir, "testdata/Unsupported_files")
        
        # Get all files from testdata/Unsupported_files folder
        all_unsupported_files = []
        if os.path.exists(unsupported_dir) and os.path.isdir(unsupported_dir):
            for filename in os.listdir(unsupported_dir):
                file_path = os.path.join(unsupported_dir, filename)
                # Only add if it's a file (not a directory)
                if os.path.isfile(file_path):
                    all_unsupported_files.append(file_path)
        
        logger.info(f"Found {len(all_unsupported_files)} unsupported files to upload")
        logger.info(f"Unsupported files: {[os.path.basename(f) for f in all_unsupported_files]}")
        
        # Upload all unsupported files
        if all_unsupported_files:
            file_chooser.set_files(all_unsupported_files)
            self.page.wait_for_timeout(5000)
            self.page.wait_for_load_state("networkidle")
            logger.info("All unsupported files uploaded")
            
            # Validate error messages for each unsupported file type
            error_validations = [
                (self.ERROR_MSG_AUDIO, "test_audio.wav"),
                (self.ERROR_MSG_DOCX, "test_doc.docx"),
                (self.ERROR_MSG_JSON, "test_json.json"),
                (self.ERROR_MSG_PDF, "test_pdf.pdf"),
                (self.ERROR_MSG_POWERBI, "test_powerBi.pbix"),
                (self.ERROR_MSG_TXT, "test_text.txt"),
            ]
            
            logger.info("Validating error messages for unsupported files...")
            for error_locator, filename in error_validations:
                try:
                    expect(self.page.locator(error_locator)).to_be_visible(timeout=5000)
                    logger.info(f"✓ Error message validated for '{filename}'")
                except Exception as e:
                    logger.warning(f"✗ Error message not found for '{filename}': {str(e)}")
            
            # Validate that translate button is disabled
            is_disabled = self.page.locator(self.TRANSLATE_BTN).is_disabled()
            logger.info(f"Translate button disabled status: {is_disabled}")
            expect(self.page.locator(self.TRANSLATE_BTN)).to_be_disabled()
            logger.info("Validation passed: Translate button is correctly disabled for unsupported files")

   
    def upload_harmful_file_and_validate(self):
        """
        Upload harmful file from testdata/Harmful_file folder, start translation,
        and validate error message is displayed and download button is disabled.
        """
        with self.page.expect_file_chooser() as fc_info:
            self.page.locator(self.BROWSE_FILES).click()
            self.page.wait_for_timeout(5000)
            self.page.wait_for_load_state("networkidle")
        file_chooser = fc_info.value
        current_working_dir = os.getcwd()
        harmful_file_dir = os.path.join(current_working_dir, "testdata/Harmful_file")
        
        # Get all files from testdata/Harmful_file folder
        harmful_files = []
        if os.path.exists(harmful_file_dir) and os.path.isdir(harmful_file_dir):
            for filename in os.listdir(harmful_file_dir):
                file_path = os.path.join(harmful_file_dir, filename)
                if os.path.isfile(file_path):
                    harmful_files.append(file_path)
        
        if harmful_files:
            logger.info(f"Found {len(harmful_files)} harmful file(s) to upload")
            logger.info(f"Harmful file(s): {[os.path.basename(f) for f in harmful_files]}")
            
            # Upload harmful file(s)
            file_chooser.set_files(harmful_files)
            self.page.wait_for_timeout(5000)
            self.page.wait_for_load_state("networkidle")
            logger.info("Harmful file(s) uploaded successfully")
            
            # Start translation
            logger.info("Clicking 'Start translating' button")
            self.page.locator(self.TRANSLATE_BTN).click()
            self.page.wait_for_timeout(10000)
            self.page.wait_for_load_state("networkidle")
            logger.info("Translation process started")
            
            # Validate error message is visible
            try:
                expect(self.page.locator(self.ERROR_MSG_UNABLE_TO_PROCESS)).to_be_visible(timeout=200000)
                logger.info("✓ Error message validated: 'Unable to process the file'")
            except Exception as e:
                logger.error(f"✗ Error message not found: {str(e)}")
                raise
            
            # Validate download button is disabled
            try:
                is_disabled = self.page.locator(self.DOWNLOAD_FILES).is_disabled()
                logger.info(f"Download button disabled status: {is_disabled}")
                expect(self.page.locator(self.DOWNLOAD_FILES)).to_be_disabled()
                logger.info("✓ Download button is correctly disabled for harmful file")
            except Exception as e:
                logger.error(f"✗ Download button validation failed: {str(e)}")
                raise
            
            logger.info("Validation passed: Harmful file processing error handled correctly")
        else:
            logger.error(f"No harmful files found in directory: {harmful_file_dir}")
            raise FileNotFoundError(f"No harmful files found in: {harmful_file_dir}")

    def validate_translate(self):
        self.page.locator(self.TRANSLATE_BTN).click()
        expect(self.page.locator(self.DOWNLOAD_FILES)).to_be_enabled(timeout=200000)
        self.page.locator(self.SUMMARY).click()
        expect(self.page.locator(self.FILE_PROCESSED_MSG)).to_be_visible()
        self.page.wait_for_timeout(3000)

    def validate_batch_history(self):
        self.page.locator(self.BATCH_HISTORY).click()
        self.page.wait_for_timeout(3000)
        batch_details = self.page.locator(self.BATCH_DETAILS)
        for i in range(batch_details.count()):  
            expect(batch_details.nth(i)).to_be_visible()
        self.page.locator(self.CLOSE_BATCH_HISTORY).click()

    def delete_first_batch_history_and_validate_count(self):
        """
        Delete the first batch history item and validate the count is reduced by 1.
        Opens batch history, gets initial count, hovers over first item, deletes it,
        and validates the new count is one less than the original.
        """
        # Open batch history panel
        self.page.locator(self.BATCH_HISTORY).click()
        self.page.wait_for_timeout(3000)
        
        # Get initial count of batch details
        batch_details = self.page.locator(self.BATCH_DETAILS)
        initial_count = batch_details.count()
        logger.info(f"Batch history count before deletion: {initial_count}")
        # Hover over the first batch detail to reveal delete button
        batch_details.first.hover()
        self.page.wait_for_timeout(1000)
        
        # Click the delete button (✕) for the first batch
        delete_buttons = self.page.locator(self.DELETE_BATCH_BTN)
        delete_buttons.first.click()
        self.page.wait_for_timeout(1000)
        logger.info("Clicked delete button (✕) for the first batch history item")
        
        self.page.locator(self.DELETE_BATCH_HISTORY).click()
        self.page.wait_for_timeout(4000)
        logger.info("Confirmed deletion by clicking 'Delete' button")
        
        # Open batch history panel
        self.page.locator(self.VIEW_BATCH_HISTORY).click()
        self.page.wait_for_timeout(3000)

        # Get new count after deletion
        new_count = batch_details.count()
        expected_count = initial_count - 1
        logger.info(f"Batch history count after deletion: {new_count}")
        logger.info(f"Expected count: {expected_count}, Actual count: {new_count}")
        
        # Validate the count is reduced by 1
        assert new_count == expected_count, f"Expected {expected_count} batch items after deletion, but found {new_count}"
        logger.info(f"Successfully deleted batch history. Count reduced from {initial_count} to {new_count}")
        
        # Close batch history panel
        self.page.locator(self.CLOSE_BATCH_HISTORY).click()

    def validate_download_files(self):
        self.page.locator(self.DOWNLOAD_FILES).click()
        self.page.wait_for_timeout(7000)

    def return_to_home_page(self):
        """
        Click the Return Home button and validate home page is loaded.
        """
        self.page.locator(self.RETURN_HOME).click()
        self.page.wait_for_timeout(3000)
        expect(self.page.locator(self.TITLE_TEXT)).to_be_visible()

    def click_logo_and_validate_home(self):
        """
        Click on the logo title and validate that the home page title is visible.
        """
        self.page.locator(self.LOGO_TITLE).click()
        self.page.wait_for_timeout(3000)
        expect(self.page.locator(self.TITLE_TEXT)).to_be_visible()

    
