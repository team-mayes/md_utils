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


class TestReplaceColFailWell(unittest.TestCase):
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


class TestReplaceCol(unittest.TestCase):
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
