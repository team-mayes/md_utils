import unittest
import os
import logging
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
from md_utils.compare_col import DEF_CFG_FILE, main

__author__ = 'hbmayes'

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'compare_col')

# Input files #

DEF_BASE = os.path.join(SUB_DATA_DIR, "median_sum_4.5_ph4.5both.csv")
DEF_COMPARE = os.path.join(SUB_DATA_DIR, 'sum_4.5_ph4.5both.csv')
MISSING_COMPARE = os.path.join(SUB_DATA_DIR, 'missing_some_4.5_ph4.5both.csv')

# Output files #

# noinspection PyUnresolvedReferences
RMSD_OUT = os.path.join(SUB_DATA_DIR, "rmsd_sum_4.5_ph4.5both.csv")
GOOD_RMSD_OUT = os.path.join(SUB_DATA_DIR, "good_rmsd_sum_4.5_ph4.5both.csv")


class TestCompareColFailWell(unittest.TestCase):
    def testNoArgs(self):
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            # Error in looking for ini file
            self.assertTrue("Problems reading file" in output)

    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoSuchFile(self):
        test_input = ["-f", "ghost.csv", "-b", DEF_BASE]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problems reading file" in output)

    def testMissingCol(self):
        test_input = ["-f", MISSING_COMPARE, "-b", DEF_BASE]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not find key" in output)


class TestCompareCol(unittest.TestCase):
    def testDefInp(self):
        try:
            test_input = ["-f", DEF_COMPARE, "-b", DEF_BASE]
            main(test_input)
            self.assertFalse(diff_lines(RMSD_OUT, GOOD_RMSD_OUT))
        finally:
            silent_remove(RMSD_OUT, disable=DISABLE_REMOVE)

