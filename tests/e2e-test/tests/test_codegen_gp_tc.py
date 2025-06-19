import logging
import time
from pages.HomePage import HomePage

import pytest

logger = logging.getLogger(__name__)

# Define step-wise test actions for Golden Path
golden_path_steps = [
    ("01. Validate home page is loaded", lambda home: home.validate_home_page()),
    ("02. Validate Upload of other than SQL files", lambda home: home.upload_unsupported_files()),
    ("03. Validate Upload input files for SQL only", lambda home: home.upload_files()),
    ("04. Validate translation process for uploaded files", lambda home: _timed_translation(home)),
    ("05. Check batch history", lambda home: home.validate_batch_history()),
    ("06. Download all files and return home", lambda home: home.validate_download_files()),
]


def _timed_translation(home):
    start = time.time()
    home.validate_translate()
    end = time.time()
    logger.info(f"Translation process for uploaded files took {end - start:.2f} seconds")

@pytest.mark.parametrize("description, action", golden_path_steps, ids=[desc for desc, _ in golden_path_steps])
def test_codegen_golden_path(login_logout, description, action, request):
    """
    Executes golden path test steps for Modernize Your Code Accelerator with detailed logging.
    """
    request.node._nodeid = description  # To improve test output readability

    page = login_logout
    home = HomePage(page)

    logger.info(f"Running test step: {description}")
    try:
        action(home)
    except Exception:
        logger.error(f"Step failed: {description}", exc_info=True)
        raise

    # Optional reporting hook
    request.node._report_sections.append(("call", "log", f"Step passed: {description}"))
