# coding=utf-8

"""
Tests align_on_col
"""
import os
import unittest
import logging
from md_utils.align_on_col import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.dirname(TEST_DIR)
DATA_DIR = os.path.join(TEST_DIR, 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'align_col')

DEF_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list.txt')
MULTI_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_multi.txt')
NO_OVER_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_no_overlap.txt')
DUP_COL_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_dup_col.txt')
NO_COL_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_no_timestep.txt')
NO_FILE_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_no_file.txt')

# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(MAIN_DIR, 'combined_data.csv')

GOOD_OUT = os.path.join(SUB_DATA_DIR, 'align12_output_good.csv')
GOOD_MULTI_OUT = os.path.join(SUB_DATA_DIR, 'combined_data_multi_good.csv')


class TestAlignColNoOutput(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(main, []) as output:
            self.assertTrue("optional arguments" in output)
        with capture_stderr(main, []) as output:
            self.assertTrue("Problems reading file" in output)

    def testNoFile(self):
        with capture_stderr(main, ["-f", NO_FILE_CMP_LIST]) as output:
            self.assertTrue("No such file or directory" in output)


class TestAlignCol(unittest.TestCase):

    def testDefIni(self):
        try:
            main(["-f", DEF_CMP_LIST])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testMultiIni(self):
        try:
            main(["-f", MULTI_CMP_LIST])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_MULTI_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testNoOverlap(self):
        with capture_stderr(main, ["-f", NO_OVER_CMP_LIST]) as output:
            self.assertTrue("Problems reading data" in output)
        silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testDupCol(self):
        test_input = ["-f", DUP_COL_CMP_LIST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
            self.assertTrue("Non-unique column" in output)
        silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testNoTimestep(self):
        with capture_stderr(main, ["-f", NO_COL_CMP_LIST]) as output:
            self.assertTrue("Could not find value" in output)
        silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)
