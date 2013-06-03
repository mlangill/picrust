#!/usr/bin/env python
#
# suite of biom format unit tests.
# run suite by executing this file
# addapted from PyCogent and biom-format alltests.py
# https://github.com/pycogent
# https://github.com/biom-format/

#import sys, os
from os import walk, environ
from sys import exit
#from os.path import split, splitext, join, exists, abspath
from os.path import join, abspath, dirname, exists, split
import re
from glob import glob
import cogent.util.unit_test as unittest
from picrust.util import get_picrust_project_dir, system_call

__author__ = "Greg Caporaso"
__copyright__ = "Copyright 2011-2013, The PICRUSt Project"
__credits__ = ["Jose Carlos Clemente Litran", "Daniel McDonald",
               "Greg Caporaso", "Jai Ram Rideout"]
__license__ = "GPL"
__version__ = "0.9.1-dev"
__maintainer__ = "Greg Caporaso"
__email__ = "gregcaporaso@gmail.com"

from cogent.util.option_parsing import parse_command_line_parameters, make_option

script_info = {}
script_info['brief_description'] = ""
script_info['script_description'] = ""
script_info['script_usage'] = [("","","")]
script_info['output_description']= ""
script_info['required_options'] = []
script_info['optional_options'] = [
 make_option('--suppress_unit_tests',
             action='store_true',
             help='suppress unit tests [default: %default]',
             default=False),
 make_option('--suppress_script_usage_tests',
             action='store_true',
             help='suppress script usage tests [default: %default]',
             default=False),
 make_option('--unittest_glob',
             help='wildcard pattern to match tests to run [default: run all]',
             default=None),
 make_option('--script_usage_tests',
             help='comma-separated list of tests to run [default: run all]',
             default=None),
]
script_info['version'] = __version__
script_info['help_on_no_arguments'] = False

def main():
    option_parser, opts, args =\
       parse_command_line_parameters(**script_info)

    if (opts.suppress_unit_tests and opts.suppress_script_usage_tests):
       option_parser.error("You're suppressing both test types. Nothing to run.")

    test_dir = abspath(dirname(__file__))

    unittest_good_pattern = re.compile('OK\s*$')
    application_not_found_pattern = re.compile('ApplicationNotFoundError')
    python_name = 'python'
    bad_tests = []
    missing_application_tests = []

    # Run through all of PICRUSt's unit tests, and keep track of any files which
    # fail unit tests.
    if not opts.suppress_unit_tests:
        unittest_names = []
        if not opts.unittest_glob:
            for root, dirs, files in walk(test_dir):
                for name in files:
                    if name.startswith('test_') and name.endswith('.py'):
                        unittest_names.append(join(root,name))
        else:
            for fp in glob(opts.unittest_glob):
                fn = split(fp)[1]
                if fn.startswith('test_') and fn.endswith('.py'):
                    unittest_names.append(abspath(fp))

        unittest_names.sort()

        for unittest_name in unittest_names:
            print "Testing %s:\n" % unittest_name
            command = '%s %s -v' % (python_name, unittest_name)
            stdout, stderr, return_value = system_call(command)
            print stderr
            if not unittest_good_pattern.search(stderr):
                if application_not_found_pattern.search(stderr):
                    missing_application_tests.append(unittest_name)
                else:
                    bad_tests.append(unittest_name)

    if not opts.suppress_script_usage_tests:  
        try:
            from qiime.test import run_script_usage_tests
        except ImportError:
            print "QIIME not installed so not running script tests."
            opts.suppress_script_usage_tests=True
        else:
            test_data_dir = join(get_picrust_project_dir(),'picrust_test_data')
            scripts_dir  = join(get_picrust_project_dir(),'scripts')
            if opts.script_usage_tests != None:
                script_usage_tests = opts.script_usage_tests.split(',')
            else:
                script_usage_tests = None

            # Run the script usage testing functionality
                script_usage_result_summary, num_script_usage_example_failures = \
                    run_script_usage_tests(
                    qiime_test_data_dir=test_data_dir,
                    qiime_scripts_dir=scripts_dir,
                    working_dir='/tmp/',
                    verbose=True,
                    tests=script_usage_tests,
                    failure_log_fp=None,
                    force_overwrite=True,
                    timeout=240)

    print "==============\nResult summary\n=============="

    if not opts.suppress_unit_tests:
        print "\nUnit test result summary\n------------------------\n"
        if bad_tests:
            print "\nFailed the following unit tests.\n%s" % '\n'.join(bad_tests)
    
        if missing_application_tests:
            print "\nFailed the following unit tests, in part or whole due "+\
            "to missing external applications.\nDepending on the PICRUSt features "+\
            "you plan to use, this may not be critical.\n%s"\
             % '\n'.join(missing_application_tests)
        
        if not (missing_application_tests or bad_tests):
            print "\nAll unit tests passed.\n\n"

    if not opts.suppress_script_usage_tests:
        print "\nScript usage test result summary\n------------------------------------\n"
        print script_usage_result_summary
        print ""

    # If script usage tests weren't suppressed,we can't have any failures.
    script_usage_tests_success = (opts.suppress_script_usage_tests or
                                  num_script_usage_example_failures == 0)

    # If any of the unit tests or script usage tests fail, or if we have any
    # missing application errors, use return code 1 (as python's unittest
    # module does to indicate one or more failures).
    return_code = 1
    if (len(bad_tests) == 0 and len(missing_application_tests) == 0 and
        script_usage_tests_success):
        return_code = 0
    return return_code

if __name__ == "__main__":
    exit(main())
