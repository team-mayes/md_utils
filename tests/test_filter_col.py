import unittest
import os
import logging
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
from md_utils.filter_col import DEF_ARRAY_FILE, DEF_CFG_FILE, main

__author__ = 'hmayes'

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'filter_col')

# Input files #

DEF_INPUT = os.path.join(SUB_DATA_DIR, DEF_ARRAY_FILE)
NON_FLOAT_INPUT = os.path.join(SUB_DATA_DIR, 'sum_2016-04-05_dru_san_ph4.5_short.csv')
DEF_INI = os.path.join(SUB_DATA_DIR, DEF_CFG_FILE)
INVALID_KEY_INI = os.path.join(SUB_DATA_DIR, "invalid_key.ini")
INVALID_HEADER_INI = os.path.join(SUB_DATA_DIR, "no_such_header.ini")
DUP_KEY_INI = os.path.join(SUB_DATA_DIR, "filter_col_dup_col.ini")
NONE_KEPT_INI = os.path.join(SUB_DATA_DIR, "filter_col_keep_none.ini")
NO_MIN_INI = os.path.join(SUB_DATA_DIR, "filter_col_no_min.ini")
PARSE_ERROR_INI = os.path.join(SUB_DATA_DIR, "filter_col_parse_error.ini")
NONFLOAT_KEY_INI = os.path.join(SUB_DATA_DIR, "filter_col_nonfloat.ini")
BIN_INPUT = os.path.join(SUB_DATA_DIR, "combined_data.csv")
BIN_INI = os.path.join(SUB_DATA_DIR, "filter_col_bin.ini")
BIN_MAX_INI = os.path.join(SUB_DATA_DIR, "filter_col_bin_max.ini")
BIN_MAX2_INI = os.path.join(SUB_DATA_DIR, "filter_col_bin_max2.ini")
BIN_NEG_INT_INI = os.path.join(SUB_DATA_DIR, "filter_col_bin_neg_int.ini")
BIN_NONFLOAT_INI = os.path.join(SUB_DATA_DIR, "filter_col_bin_not_float.ini")
BIN_NONINT_INI = os.path.join(SUB_DATA_DIR, "filter_col_bin_not_int.ini")
BIN_TOO_FEW_INI = os.path.join(SUB_DATA_DIR, "filter_col_bin_too_few.ini")
BIN_TOO_MANY_INI = os.path.join(SUB_DATA_DIR, "filter_col_bin_too_many.ini")
TYPO_INI = os.path.join(SUB_DATA_DIR, "filter_col_typo.ini")

# Output files #

# noinspection PyUnresolvedReferences
CSV_OUT = os.path.join(SUB_DATA_DIR, "filtered_column_data.csv")
GOOD_CSV_OUT = os.path.join(SUB_DATA_DIR, "filtered_column_data_good.csv")
GOOD_CSV_NONE_KEPT = os.path.join(SUB_DATA_DIR, "filtered_column_none_kept.csv")
GOOD_NO_MIN_OUT = os.path.join(SUB_DATA_DIR, "filtered_column_max_only_good.csv")
# noinspection PyUnresolvedReferences
NON_FLOAT_OUT = os.path.join(SUB_DATA_DIR, "filtered_sum_2016-04-05_dru_san_ph4.5_short.csv")
GOOD_NON_FLOAT_OUT = os.path.join(SUB_DATA_DIR, "filtered_sum_2016-04-05_dru_san_ph4.5_short_good.csv")
DEF_BIN_OUT = os.path.join(SUB_DATA_DIR, "filtered_combined_data.csv")
GOOD_BIN_OUT = os.path.join(SUB_DATA_DIR, "filtered_combined_bin_good.csv")
GOOD_BIN_MAX_OUT = os.path.join(SUB_DATA_DIR, "filtered_combined_bin_max_good.csv")
GOOD_BIN_MAX2_OUT = os.path.join(SUB_DATA_DIR, "filtered_combined_bin_max2_good.csv")


class TestFilterColFailWell(unittest.TestCase):
    def testNoArgs(self):
        with capture_stderr(main, []) as output:
            self.assertTrue("Could not read file {}".format(DEF_CFG_FILE) in output)

    def testHelp(self):
        test_input = ["-h"]
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
                self.assertTrue("No filtering will be applied" in output)
            self.assertFalse(diff_lines(CSV_OUT, DEF_INPUT))
        finally:
            silent_remove(CSV_OUT, disable=DISABLE_REMOVE)

    def testWrongFileToFilter(self):
        # If put a configuration file as the file to read, fail well
        test_input = ["-f", DEF_INI, "-c", DEF_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("could not convert string" in output)

    def testInvalidKey(self):
        test_input = ["-f", DEF_INPUT, "-c", INVALID_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Unexpected key" in output)

    def testInvalidHeader(self):
        with capture_stderr(main, ["-f", DEF_INPUT, "-c", INVALID_HEADER_INI]) as output:
            self.assertTrue("found in configuration file but not in data file" in output)

    def testNonfloatKeyValue(self):
        test_input = ["-f", DEF_INPUT, "-c", NONFLOAT_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("For section 'min_vals' key 'z', could not convert value '' to a float" in output)

    def testParseError(self):
        # This input has a line with only "z" (no equals), resulting in a parsing error we will catch
        test_input = ["-f", DEF_INPUT, "-c", PARSE_ERROR_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("contains parsing errors" in output)
            self.assertTrue("'z" in output)

    def testBinNegInt(self):
        test_input = ["-f", DEF_INPUT, "-c", BIN_NEG_INT_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("positive integers are required" in output)

    def testBinNonfloat(self):
        test_input = ["-f", DEF_INPUT, "-c", BIN_NONFLOAT_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("could not convert '' to" in output)

    def testBinNonInt(self):
        test_input = ["-f", DEF_INPUT, "-c", BIN_NONINT_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("could not convert '0.2' to" in output)

    def testBinTooFew(self):
        test_input = ["-f", DEF_INPUT, "-c", BIN_TOO_FEW_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Expected a comma-separated list of length 3 or 4 for section "
                            "'bin_settings' key 'cv'. Read: 0.5,0.7" in output)

    def testBinTooMany(self):
        test_input = ["-f", DEF_INPUT, "-c", BIN_TOO_MANY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Expected a comma-separated list of length 3 or 4 for section 'bin_settings' key 'cv'. "
                            "Read: 0.5,0.7,2,6,10" in output)

    def testDupKey(self):
        # Checking what happens if the key is listed twice. In Python 2, the program used the last
        # key value, resulting in no rows that meet the criteria. In Python 3, the program throws an exception.
        test_input = ["-f", DEF_INPUT, "-c", DUP_KEY_INI]
        try:
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stderr(main, test_input) as output:
                self.assertTrue("already exists" in output)
        finally:
            silent_remove(CSV_OUT, disable=DISABLE_REMOVE)


class TestFilterCol(unittest.TestCase):
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
        try:
            main(test_input)
            self.assertFalse(diff_lines(NON_FLOAT_OUT, GOOD_NON_FLOAT_OUT))
        finally:
            silent_remove(NON_FLOAT_OUT)

    def testNoRowsKept(self):
        # In this case, it results in no rows that meet the criteria
        test_input = ["-f", DEF_INPUT, "-c", NONE_KEPT_INI]
        main(test_input)
        try:
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("Keeping 0 of 4 rows based on filtering criteria" in output)
            self.assertFalse(diff_lines(CSV_OUT, GOOD_CSV_NONE_KEPT))
        finally:
            silent_remove(CSV_OUT, disable=DISABLE_REMOVE)

    def testBin(self):
        test_input = ["-f", BIN_INPUT, "-c", BIN_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue("Keeping 14 of 16 rows based on filtering criteria" in output)
            self.assertFalse(diff_lines(DEF_BIN_OUT, GOOD_BIN_OUT))
        finally:
            silent_remove(DEF_BIN_OUT, disable=DISABLE_REMOVE)

    def testBinMax(self):
        # In this input, one big has more than the max and one less
        test_input = ["-f", BIN_INPUT, "-c", BIN_MAX_INI]
        try:
            main(test_input)
            # self.assertFalse(diff_lines(DEF_BIN_OUT, GOOD_BIN_MAX_OUT))
        finally:
            silent_remove(DEF_BIN_OUT, disable=DISABLE_REMOVE)

    def testBinMax2(self):
        # In this input, both bins have more than the max entries
        test_input = ["-f", BIN_INPUT, "-c", BIN_MAX2_INI]
        try:
            main(test_input)
            self.assertFalse(diff_lines(DEF_BIN_OUT, GOOD_BIN_MAX2_OUT))
        finally:
            silent_remove(DEF_BIN_OUT, disable=DISABLE_REMOVE)
