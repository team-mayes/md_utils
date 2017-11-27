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
MULTI_FILE_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_4files.txt')
MULTI_LINE_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_multi_lines.txt')
NO_OVER_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_no_overlap.txt')
DUP_COL_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_dup_col.txt')
NO_COL_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_no_timestep.txt')
NO_FILE_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_no_file.txt')

# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(MAIN_DIR, 'comb.csv')

GOOD_OUT = os.path.join(SUB_DATA_DIR, 'align12_output_good.csv')
GOOD_MULTI_FILE_OUT = os.path.join(SUB_DATA_DIR, 'combined_multi_good.csv')
GOOD_MULTI_LINE_OUT = os.path.join(SUB_DATA_DIR, 'combined_multi_line_good.csv')
LINE1_OUT = os.path.join(SUB_DATA_DIR, '0.750_20c_comb.csv')
GOOD_LINE1_OUT = os.path.join(SUB_DATA_DIR, '0.750_20c_comb_good.csv')
LINE2_OUT = os.path.join(SUB_DATA_DIR, '0.875_20c_comb.csv')
GOOD_LINE2_OUT = os.path.join(SUB_DATA_DIR, '0.875_20c_comb_good.csv')
LINE3_OUT = os.path.join(SUB_DATA_DIR, '2_comb.csv')
LINE4_OUT = os.path.join(SUB_DATA_DIR, '3_comb.csv')


class TestAlignColNoOutput(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(main, []) as output:
            self.assertTrue("optional arguments" in output)
        with capture_stderr(main, []) as output:
            self.assertTrue("Problems reading file" in output)

    def testNoFile(self):
        with capture_stderr(main, ["-f", NO_FILE_CMP_LIST]) as output:
            self.assertTrue("Did not find file" in output)

    def testNoTimestep(self):
        test_input = ["-f", NO_COL_CMP_LIST]
        main(test_input)
        # with capture_stderr(main, test_input) as output:
        #     self.assertTrue("Could not find value" in output)
        silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testNoOverlap(self):
        with capture_stderr(main, ["-f", NO_OVER_CMP_LIST]) as output:
            self.assertTrue("Problems reading data" in output)
        silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testUnregArg(self):
        test_input = ['-@@@', "-f", DEF_CMP_LIST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("unrecognized arguments" in output)


class TestAlignCol(unittest.TestCase):

    def testDefIni(self):
        try:
            main(["-f", DEF_CMP_LIST])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testMultiFileIni(self):
        try:
            main(["-f", MULTI_FILE_CMP_LIST])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_MULTI_FILE_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testDupCol(self):
        test_input = ["-f", DUP_COL_CMP_LIST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
            self.assertTrue("Non-unique column" in output)
        silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testMultiLineIni(self):
        try:
            main(["-f", MULTI_LINE_CMP_LIST])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_MULTI_LINE_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testMultiLineSepIni(self):
        # have different rows create different files
        # test that if the prefix is already used, number it
        # test if nothing common in the file base names, number it
        try:
            main(["-f", MULTI_LINE_CMP_LIST, "-s", "-l", SUB_DATA_DIR])
            self.assertFalse(diff_lines(LINE1_OUT, GOOD_LINE1_OUT))
            self.assertFalse(diff_lines(LINE2_OUT, GOOD_LINE2_OUT))
            self.assertFalse(diff_lines(LINE3_OUT, GOOD_LINE1_OUT))
            self.assertFalse(diff_lines(LINE4_OUT, GOOD_LINE1_OUT))
        finally:
            silent_remove(LINE1_OUT, disable=DISABLE_REMOVE)
            silent_remove(LINE2_OUT, disable=DISABLE_REMOVE)
            silent_remove(LINE3_OUT, disable=DISABLE_REMOVE)
            silent_remove(LINE4_OUT, disable=DISABLE_REMOVE)
