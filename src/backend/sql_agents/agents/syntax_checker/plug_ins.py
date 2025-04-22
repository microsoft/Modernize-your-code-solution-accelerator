"""This module contains the plug-in functions for the SQL agent."""

import logging
import os
import platform
import subprocess
from typing import Annotated

from semantic_kernel.functions import kernel_function

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Define a sample plugin for the sample
class SyntaxCheckerPlugin:
    """Contains plug-in functions which can be called by agents."""

    @kernel_function(
        description="Checks to see if there are errors in the TSQL syntax of the input."
    )
    def check_syntax(
        self,
        candidate_sql: Annotated[
            str, "The TSQL that needs to be checked for syntax issues"
        ],
    ) -> Annotated[
        str,
        """
        Returns a json list of errors in the format of.
        [
            {
                "Line": <line number>,
                "Column": <column number>,
                "Error": <error message>
            }
        ]
        or an empty list if there are no errors.
        """,
    ]:
        """Check the TSQL syntax using tsqlParser."""
        print(f"Called syntaxCheckerPlugin with: {candidate_sql}")
        return self._call_tsqlparser(candidate_sql)

    def _call_tsqlparser(self, param):
        """Select the executable based on the operating system."""
        print("cwd =" + os.getcwd())
        print(f"Calling tsqlParser with: {param}")
        if platform.system() == "Windows":
            exe_path = r".\sql_agents\tools\win-x64\tsqlParser.exe"
            # exe_path = r".\src\backend\agents\tools\win-x64\tsqlParser.exe"
        else:
            exe_path = "./sql_agents/tools/linux-x64/tsqlParser"

        # Build the command with the parameter
        cmd = [exe_path, "--string", str(param)]

        try:
            # Note that there are issues running asyncio.create_subprocess_exec on with uvicorn that prevent VS Code debugging
            # from working correctly. So we are using subprocess.run instead.

            # Run the executable synchronously
            rslt = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(rslt.stdout)
            return rslt.stdout
        except subprocess.CalledProcessError as e:
            # Log or handle the error as needed
            print("Error running executable:", e)
            return ""
        except Exception as e:
            print(f"Error:{e.__doc__}")
            return None
