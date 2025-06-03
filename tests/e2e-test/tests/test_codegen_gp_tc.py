import logging
import time

from pages.HomePage import HomePage

import pytest


logger = logging.getLogger(__name__)


@pytest.mark.testcase_id("TC001")
def test_CodeGen_Golden_path_test(login_logout):
    """Validate Golden path test case for Modernize your code Accelerator"""
    page = login_logout
    home_page = HomePage(page)
    logger.info("Step 1: Validate home page is loaded.")
    home_page.validate_home_page()
    logger.info("Step 2: Validate Upload of other than SQL files.")
    home_page.upload_unsupported_files()
    logger.info("Step 3: Validate Upload input files for SQL only.")
    home_page.upload_files()
    logger.info("Step 4: Validate translation process for uploaded files.")
    start = time.time()
    home_page.validate_translate()
    end = time.time()
    print(f"Translation process for uploaded files took {end - start:.2f} seconds")
    logger.info("Step 5: Check batch history.")
    home_page.validate_batch_history()
    logger.info("Step 6: Download all files and return home.")
    home_page.validate_download_files()
