import os
import sys

# Determine the project root relative to this conftest.py file.
# This file is at: <project_root>/src/tests/conftest.py
# We want to add: <project_root>/src/backend to sys.path.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))  # Goes from tests to src
backend_path = os.path.join(project_root, "backend")
sys.path.insert(0, backend_path)

print("Adjusted sys.path:", sys.path)
