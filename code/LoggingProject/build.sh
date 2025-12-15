#!/bin/bash
set -e  # Exit immediately if any command fails


pip3 install coverage pytest pytest-django radon
pip install django-tailwind
pip install django-browser-reload

echo "Starting Django CI Pipeline"

cd LoggingProject || { echo "Failed to change directory to LoggingProject"; exit 1; }
#echo "Running Django Unit Tests"
#python3 manage.py test || { echo "Unit tests failed"; exit 1; }
#paver test
echo "Running Coverage Tests"
python3 -m coverage run --source='.' manage.py test --verbosity=2 || { echo "Coverage tests failed"; exit 1; }

echo "Generating Coverage Report"
python3 -m coverage report || { echo "Failed to generate coverage report"; exit 1; }
python3 -m coverage xml -o coverage.xml || { echo "Failed to generate XML coverage report"; exit 1; }

echo "Running Radon Complexity Analysis"
radon cc LogApp/ -s > radon_analysis.txt

# Show Radon Complexity Summary
echo "Radon Complexity Summary:"
# Fail if any function/class has a complexity rating of C or higher
if grep -E '\([C-F]\)' radon_analysis.txt; then
    echo "Build failed: Radon found functions/classes with complexity C or higher."
    exit 1
fi

cat radon_analysis.txt

echo "Django tests, coverage, and complexity checks complete."
