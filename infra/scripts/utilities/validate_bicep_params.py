from pathlib import Path
import runpy
import sys

script_path = Path(__file__).resolve().parents[3] / 'scripts' / 'validate_bicep_params.py'
sys.path[0] = str(script_path.parent)
runpy.run_path(str(script_path), run_name='__main__')
