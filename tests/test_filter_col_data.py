import unittest
import os
import logging
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
from md_utils.filter_col_data import DEF_ARRAY_FILE, DEF_CFG_FILE, main

__author__ = 'hmayes'

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'filter_col_data')

# Input files #

DEF_INPUT = os.path.join(SUB_DATA_DIR, DEF_ARRAY_FILE)
NON_FLOAT_INPUT = os.path.join(SUB_DATA_DIR, 'sum_2016-04-05_dru_san_ph4.5_short.csv')
DEF_INI = os.path.join(SUB_DATA_DIR, DEF_CFG_FILE)
INVALID_KEY_INI = os.path.join(SUB_DATA_DIR, "invalid_key.ini")
INVALID_HEADER_INI = os.path.join(SUB_DATA_DIR, "no_such_header.ini")
NO_MIN_INI = os.path.join(SUB_DATA_DIR, "filter_col_data_no_min.ini")

# Output files #

# noinspection PyUnresolvedReferences
CSV_OUT = os.path.join(SUB_DATA_DIR, "filtered_column_data.csv")
GOOD_CSV_OUT = os.path.join(SUB_DATA_DIR, "filtered_column_data_good.csv")
GOOD_NO_MIN_OUT = os.path.join(SUB_DATA_DIR, "filtered_column_max_only_good.csv")
# noinspection PyUnresolvedReferences
NON_FLOAT_OUT = os.path.join(SUB_DATA_DIR, "filtered_sum_2016-04-05_dru_san_ph4.5_short.csv")
GOOD_NON_FLOAT_OUT = os.path.join(SUB_DATA_DIR, "filtered_sum_2016-04-05_dru_san_ph4.5_short_good.csv")


class TestPerColFailWell(unittest.TestCase):
    def testNoArgs(self):
        with capture_stderr(main, []) as output:
            self.assertTrue("Could not read file {}".format(DEF_CFG_FILE) in output)

    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testInvalidKey(self):
        test_input = ["-f", DEF_INPUT, "-c", INVALID_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Unexpected key" in output)

    def testInvalidHeader(self):
        with capture_stderr(main, ["-f", DEF_INPUT, "-c", INVALID_HEADER_INI]) as output:
            self.assertTrue("found in configuration file but not in data file" in output)


class TestPerCol(unittest.TestCase):
    def testDefInp(self):
        try:
            with capture_stdout(main, ["-f", DEF_INPUT, "-c", DEF_INI]) as output:
                self.assertTrue("Keeping 2 of 4 rows based on filtering criteria" in output)
            self.assertFalse(diff_lines(CSV_OUT, GOOD_CSV_OUT))
        finally:
            silent_remove(CSV_OUT)

    def testNoMinNonFloat(self):
        # Tests both handling when no min section is specified and non-floats in the file to be analyzed
        test_input = ["-f", NON_FLOAT_INPUT, "-c", NO_MIN_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stderr(main, test_input) as output:
                self.assertTrue("WARNING:  No 'min_vals' section. Program will continue." in output)
            self.assertFalse(diff_lines(NON_FLOAT_OUT, GOOD_NON_FLOAT_OUT))
        finally:
            silent_remove(NON_FLOAT_OUT)
