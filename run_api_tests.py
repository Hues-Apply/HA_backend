#!/usr/bin/env python
"""
Test runner script to run all API tests
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Default: run all API tests
    test_modules = [
        'tests.auth.test_auth_api',
        'tests.users.test_user_api',
        'tests.opportunities.test_opportunities_api',
        'tests.opportunities.test_tracking_api',
        'tests.opportunities.test_recommendations_api',
        'tests.applications.test_applications_api',
    ]
    
    # Allow specifying specific test modules from command line
    if len(sys.argv) > 1:
        test_modules = sys.argv[1:]
    
    failures = test_runner.run_tests(test_modules)
    sys.exit(bool(failures))
