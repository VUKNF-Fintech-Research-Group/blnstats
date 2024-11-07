#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Run the tests using Python's unittest module
# python3 -m unittest discover -s tests -p "test_*.py"
python3 -m unittest discover -s tests -p "test_coefficients.py"