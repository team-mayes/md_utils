import unittest
import os
import logging
from shutil import copyfile
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove, create_out_fname
from md_utils.replace_col import DEF_ARRAY_FILE, DEF_CFG_FILE, main

__author__ = 'hmayes'

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'replace_col')
FOLDER_A = os.path.join(SUB_DATA_DIR, '10')
FOLDER_B = os.path.join(SUB_DATA_DIR, '100')
FOLDER_C = os.path.join(SUB_DATA_DIR, '1000')
FOLDERS = [FOLDER_A, FOLDER_B, FOLDER_C]

# Input files #

DEF_INPUT = os.path.join(SUB_DATA_DIR, DEF_ARRAY_FILE)
NON_FLOAT_INPUT = os.path.join(SUB_DATA_DIR, 'sum_2016-04-05_dru_san_ph4.5_short.csv')
DEF_INI = os.path.join(SUB_DATA_DIR, DEF_CFG_FILE)
INVALID_KEY_INI = os.path.join(SUB_DATA_DIR, "invalid_key.ini")
INVALID_HEADER_INI = os.path.join(SUB_DATA_DIR, "no_such_header.ini")
DUP_KEY_INI = os.path.join(SUB_DATA_DIR, "filter_col_dup_col.ini")
NO_MIN_INI = os.path.join(SUB_DATA_DIR, "filter_col_no_min.ini")
PARSE_ERROR_INI = os.path.join(SUB_DATA_DIR, "filter_col_parse_error.ini")
NONFLOAT_KEY_INI = os.path.join(SUB_DATA_DIR, "filter_col_nonfloat.ini")

TYPO_INI = os.path.join(SUB_DATA_DIR, "replace_col_typo.ini")
TEST_BASE = "test_seed.csv"
TEST_INPUT = os.path.join(SUB_DATA_DIR, TEST_BASE)
TEMP_PREFIX = 'temp_'
TEMP_INPUT = os.path.join(SUB_DATA_DIR, TEMP_PREFIX + TEST_BASE)
GOOD_OUTPUT = os.path.join(SUB_DATA_DIR, 'good_' + TEST_BASE)
SEED_NAME = 'seed_dru_san.csv'
GOOD_NAME = 'good_' + SEED_NAME

# Output files #

# noinspection PyUnresolvedReferences
# CSV_OUT = os.path.join(SUB_DATA_DIR, "filtered_column_data.csv")
GOOD_CSV_OUT = os.path.join(SUB_DATA_DIR, "filtered_column_data_good.csv")
GOOD_CSV_NONE_KEPT = os.path.join(SUB_DATA_DIR, "filtered_column_none_kept.csv")
GOOD_NO_MIN_OUT = os.path.join(SUB_DATA_DIR, "filtered_column_max_only_good.csv")
# noinspection PyUnresolvedReferences
NON_FLOAT_OUT = os.path.join(SUB_DATA_DIR, "filtered_sum_2016-04-05_dru_san_ph4.5_short.csv")
GOOD_NON_FLOAT_OUT = os.path.join(SUB_DATA_DIR, "filtered_sum_2016-04-05_dru_san_ph4.5_short_good.csv")


# Shared Methods #

def copy_input(f_name):
    new_name = create_out_fname(f_name, prefix=TEMP_PREFIX)
    copyfile(f_name, new_name)
    print("Created file: {}".format(new_name))


class TestFilterColFailWell(unittest.TestCase):
    def testNoArgs(self):
        with capture_stderr(main, []) as output:
            # Error in looking for ini file
            self.assertTrue("Could not read file {}".format(DEF_CFG_FILE) in output)

    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoSuchFile(self):
        test_input = ["-f", "ghost.csv", "-c", DEF_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problems reading file" in output)

    def testTypoIni(self):
        # If a section name is encountered and not expected, flag it
        test_input = ["-f", DEF_INPUT, "-c", TYPO_INI]
        try:
            with capture_stderr(main, test_input) as output:
                self.assertTrue("Found section 'min', which will be ignored" in output)
                # self.assertTrue("No filtering will be applied" in output)
            # self.assertFalse(diff_lines(CSV_OUT, DEF_INPUT))
        finally:
            pass
            # silent_remove(CSV_OUT, disable=DISABLE_REMOVE)

    def testWrongFileToFilter(self):
        # If put a configuration file as the file to read, fail well
        test_input = ["-f", DEF_INI, "-c", DEF_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("could not convert string" in output)

    # def testInvalidKey(self):
    #     test_input = ["-f", DEF_INPUT, "-c", INVALID_KEY_INI]
    #     if logger.isEnabledFor(logging.DEBUG):
    #         main(test_input)
    #     with capture_stderr(main, test_input) as output:
    #         self.assertTrue("Unexpected key" in output)
    #
    # def testInvalidHeader(self):
    #     with capture_stderr(main, ["-f", DEF_INPUT, "-c", INVALID_HEADER_INI]) as output:
    #         self.assertTrue("found in configuration file but not in data file" in output)
    #
    # def testNonfloatKeyValue(self):
    #     test_input = ["-f", DEF_INPUT, "-c", NONFLOAT_KEY_INI]
    #     if logger.isEnabledFor(logging.DEBUG):
    #         main(test_input)
    #     with capture_stderr(main, test_input) as output:
    #         self.assertTrue("For section 'min_vals' key 'z', could not convert value '' to a float" in output)
    #
    # def testParseError(self):
    #     # This input has a line with only "z" (no equals), resulting in a parsing error we will catch
    #     test_input = ["-f", DEF_INPUT, "-c", PARSE_ERROR_INI]
    #     if logger.isEnabledFor(logging.DEBUG):
    #         main(test_input)
    #     with capture_stderr(main, test_input) as output:
    #         self.assertTrue("File contains parsing errors" in output)
    #         self.assertTrue("'z" in output)


class TestFilterCol(unittest.TestCase):
    def testDefInp(self):
        # testing a single file
        try:
            copy_input(TEST_INPUT)
            test_input = ["-f", TEMP_INPUT, "-c", DEF_INI]
            main(test_input)
            self.assertFalse(diff_lines(TEMP_INPUT, GOOD_OUTPUT))
        finally:
            silent_remove(TEMP_INPUT)

    def testFilePattern(self):
        # testing a single file
        try:
            for folder in FOLDERS:
                test_file = os.path.join(folder, SEED_NAME)
                copy_input(test_file)
            test_input = ["-c", DEF_INI]
            main(test_input)
            for folder in FOLDERS:
                test_output = os.path.join(folder, TEMP_PREFIX + SEED_NAME)
                good_output = os.path.join(folder, GOOD_NAME)
                self.assertFalse(diff_lines(test_output, good_output))
        finally:
            for folder in FOLDERS:
                test_output = os.path.join(folder, TEMP_PREFIX + SEED_NAME)
                silent_remove(test_output, disable=DISABLE_REMOVE)

    # def testNoMinNonFloat(self):
    #     # Tests both handling when no min section is specified and non-floats in the file to be analyzed
    #     test_input = ["-f", NON_FLOAT_INPUT, "-c", NO_MIN_INI]
    #     try:
    #         main(test_input)
    #         self.assertFalse(diff_lines(NON_FLOAT_OUT, GOOD_NON_FLOAT_OUT))
    #     finally:
    #         silent_remove(NON_FLOAT_OUT)
    #
    # def testDupKey(self):
    #     # Checking what happens if the key is listed twice. Expect the program to use the last
    #     # key value. In this case, it results in no rows that meet the criteria
    #     test_input = ["-f", DEF_INPUT, "-c", DUP_KEY_INI]
    #     try:
    #         if logger.isEnabledFor(logging.DEBUG):
    #             main(test_input)
    #         with capture_stdout(main, test_input) as output:
    #             self.assertTrue("Keeping 0 of 4 rows based on filtering criteria" in output)
    #         self.assertFalse(diff_lines(CSV_OUT, GOOD_CSV_NONE_KEPT))
    #     finally:
    #         silent_remove(CSV_OUT, disable=DISABLE_REMOVE)
