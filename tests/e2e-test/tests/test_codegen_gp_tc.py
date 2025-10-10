import logging
import time

from pages.HomePage import HomePage

import pytest

logger = logging.getLogger(__name__)


def _timed_translation(home):
    start = time.time()
    home.validate_translate()
    end = time.time()
    logger.info(f"Translation process for uploaded files took {end - start:.2f} seconds")


def test_codegen_golden_path(login_logout, request):
    """
    CodeMod- Validate Golden path works as expected
    
    Executes golden path test steps for Modernize Your Code Accelerator with detailed logging.
    """
    request.node._nodeid = "Modernize your code- Validate Golden path works as expected"
    
    page = login_logout
    home = HomePage(page)

    # Define step-wise test actions for Golden Path
    golden_path_steps = [
        ("01. Validate home page is loaded", lambda: home.validate_home_page()),
        ("02. Validate Upload of other than SQL files", lambda: home.upload_unsupported_files()),
        ("03. Validate Upload input files for SQL only", lambda: home.upload_files()),
        ("04. Validate translation process for uploaded files", lambda: _timed_translation(home)),
        ("05. Check batch history", lambda: home.validate_batch_history()),
        ("06. Download all files", lambda: home.validate_download_files()),
        ("07. Return to home page", lambda: home.return_to_home_page()),
    ]

    # Execute all steps sequentially
    for description, action in golden_path_steps:
        logger.info(f"Running test step: {description}")
        try:
            action()
            logger.info(f"Step passed: {description}")
        except Exception:
            logger.error(f"Step failed: {description}", exc_info=True)
            raise



def test_upload_all_files_and_navigate_home(login_logout, request):
    """
    CodeMod- Validate upload all files, verify count, and navigate to home page
    
    Test case that uploads all files from testdata folder, validates the uploaded
    files count is 20, and navigates back to home page.
    """
    request.node._nodeid = "Modernize your code - Validate Files uploading and its limit."
    
    page = login_logout
    home = HomePage(page)

    # Define test steps
    test_steps = [
        ("01. Validate home page is loaded", lambda: home.validate_home_page()),
        ("02. Upload all files from testdata folder", lambda: home.upload_all_files()),
        ("03. Validate uploaded files count equals 20", lambda: home.validate_uploaded_files_count()),
        ("04. Navigate back to home page", lambda: home.navigate_to_home_page()),
    ]

    # Execute all steps sequentially with logging
    for description, action in test_steps:
        logger.info(f"Running test step: {description}")
        try:
            action()
            logger.info(f"Step passed: {description}")
        except Exception:
            logger.error(f"Step failed: {description}", exc_info=True)
            raise

def test_translate_and_download_files(login_logout, request):
    """
    Modernize your code - Translating the files and downloading files
    
    Test case that executes the complete translation workflow: upload files,
    translate them, and download the results with detailed logging.
    """
    request.node._nodeid = "Modernize your code - Translating the files and downloading files"
    
    page = login_logout
    home = HomePage(page)

    # Define step-wise test actions for translation and download workflow
    test_steps = [
        ("01. Validate home page is loaded", lambda: home.validate_home_page()),
        ("02. Validate Upload of other than SQL files", lambda: home.upload_unsupported_files()),
        ("03. Validate Upload input files for SQL only", lambda: home.upload_files()),
        ("04. Validate translation process for uploaded files", lambda: _timed_translation(home)),
        ("05. Check batch history", lambda: home.validate_batch_history()),
        ("06. Download all files", lambda: home.validate_download_files()),
        ("07. Return to home page", lambda: home.click_logo_and_validate_home()),
    ]

    # Execute all steps sequentially with detailed logging
    for description, action in test_steps:
        logger.info(f"Running test step: {description}")
        try:
            action()
            logger.info(f"Step passed: {description}")
        except Exception:
            logger.error(f"Step failed: {description}", exc_info=True)
            raise



def test_upload_remove_files_and_cancel(login_logout, request):
    """
    CodeMod- Validate upload files, remove files, and cancel upload
    
    Test case that uploads 20 files from testdata folder, removes the first three files,
    validates the remaining count is 17, and then cancels the upload process.
    """
    request.node._nodeid = "Modernize your code - Validate Single and Batch deletion of Files."
    
    page = login_logout
    home = HomePage(page)

    # Define test steps
    test_steps = [
        ("01. Validate home page is loaded", lambda: home.validate_home_page()),
        ("02. Upload all files from testdata folder (20 files max)", lambda: home.upload_all_files()),
        ("03. Validate uploaded files count equals 20", lambda: home.validate_uploaded_files_count()),
        ("04. Remove first three files and validate count equals 17", lambda: home.remove_first_three_files_and_validate_count()),
        ("05. Cancel upload and validate return to home page", lambda: home.cancel_upload_and_validate_home()),
    ]

    # Execute all steps sequentially with logging
    for description, action in test_steps:
        logger.info(f"Running test step: {description}")
        try:
            action()
            logger.info(f"Step passed: {description}")
        except Exception:
            logger.error(f"Step failed: {description}", exc_info=True)
            raise


def test_delete_batch_history(login_logout, request):
    """
    CodeMod- Validate delete batch history functionality
    
    Test case that executes the golden path flow (upload, translate, download) and then
    validates the deletion of the first batch history item.
    """
    request.node._nodeid = "Modernize your code - Validate Batch history panel."
    
    page = login_logout
    home = HomePage(page)

    # Define test steps (golden path without return home + delete batch history)
    test_steps = [
        ("01. Validate home page is loaded", lambda: home.validate_home_page()),
        ("02. Validate Upload of other than SQL files", lambda: home.upload_unsupported_files()),
        ("03. Validate Upload input files for SQL only", lambda: home.upload_files()),
        ("04. Validate translation process for uploaded files", lambda: _timed_translation(home)),
        ("05. Check batch history", lambda: home.validate_batch_history()),
        ("06. Download all files", lambda: home.validate_download_files()),
        ("07. Delete first batch history and validate count", lambda: home.delete_first_batch_history_and_validate_count())
    ]

    # Execute all steps sequentially with logging
    for description, action in test_steps:
        logger.info(f"Running test step: {description}")
        try:
            action()
            logger.info(f"Step passed: {description}")
        except Exception:
            logger.error(f"Step failed: {description}", exc_info=True)
            raise


def test_upload_unsupported_files_validation(login_logout, request):
    """
    CodeMod- Validate unsupported files upload and validation
    
    Test case that uploads all unsupported files from testdata/Unsupported_files folder
    and validates that translate button is disabled with detailed logging.
    """
    request.node._nodeid = "Modernize your code - Validate Attempt to upload files with an unsupported extension"
    
    page = login_logout
    home = HomePage(page)

    # Define test steps
    test_steps = [
        ("01. Validate home page is loaded", lambda: home.validate_home_page()),
        ("02. Upload all unsupported files and validate translate button is disabled", lambda: home.upload_all_unsupported_files_and_validate()),
    ]

    # Execute all steps sequentially with logging
    for description, action in test_steps:
        logger.info(f"Running test step: {description}")
        try:
            action()
            logger.info(f"Step passed: {description}")
        except Exception:
            logger.error(f"Step failed: {description}", exc_info=True)
            raise


def test_upload_large_file_validation(login_logout, request):
    """
    CodeMod- Validate large file upload size limit
    
    Test case that uploads a large file from testdata/Large_file folder
    and validates that the 200MB size limit error message is displayed.
    """
    request.node._nodeid = "Modernize your code - Validate Attempt to upload a .sql file larger than 200 MB"
    
    page = login_logout
    home = HomePage(page)

    # Define test steps
    test_steps = [
        ("01. Validate home page is loaded", lambda: home.validate_home_page()),
        ("02. Upload large file and validate size limit error message", lambda: home.upload_large_file_and_validate()),
    ]

    # Execute all steps sequentially with logging
    for description, action in test_steps:
        logger.info(f"Running test step: {description}")
        try:
            action()
            logger.info(f"Step passed: {description}")
        except Exception:
            logger.error(f"Step failed: {description}", exc_info=True)
            raise


def test_upload_harmful_file_validation(login_logout, request):
    """
    CodeMod- Validate harmful file upload and processing error
    
    Test case that uploads harmful file from testdata/Harmful_file folder,
    starts translation, and validates error message and disabled download button.
    """
    request.node._nodeid = "Modernize your code - Validate Attempt to upload malicious files"
    
    page = login_logout
    home = HomePage(page)

    # Define test steps
    test_steps = [
        ("01. Validate home page is loaded", lambda: home.validate_home_page()),
        ("02. Upload harmful file, translate, and validate error handling", lambda: home.upload_harmful_file_and_validate()),
        ("03. Return to home page", lambda: home.return_to_home_page()),
    ]

    # Execute all steps sequentially with logging
    for description, action in test_steps:
        logger.info(f"Running test step: {description}")
        try:
            action()
            logger.info(f"Step passed: {description}")
        except Exception:
            logger.error(f"Step failed: {description}", exc_info=True)
            raise


