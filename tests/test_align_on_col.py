# coding=utf-8

"""
Tests align_on_col
"""
import os
import unittest

from md_utils import align_on_col
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'align_col')

DEF_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list.txt')
MULTI_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_multi.txt')
NO_OVER_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_no_overlap.txt')
DUP_COL_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_dup_col.txt')
NO_COL_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_no_timestep.txt')
NO_FILE_CMP_LIST = os.path.join(SUB_DATA_DIR, 'compare_list_no_file.txt')

# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(TEST_DIR, 'combined_data.csv')

GOOD_OUT = os.path.join(SUB_DATA_DIR, 'align12_output_good.csv')
GOOD_MULTI_OUT = os.path.join(SUB_DATA_DIR, 'combined_data_multi_good.csv')


class TestAlignCol(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(align_on_col.main, []) as output:
            self.assertTrue("optional arguments" in output)
        with capture_stderr(align_on_col.main, []) as output:
            self.assertTrue("Problems reading file" in output)

    def testDefIni(self):
        try:
            align_on_col.main(["-f", DEF_CMP_LIST])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT)

    def testMultiIni(self):
        try:
            align_on_col.main(["-f", MULTI_CMP_LIST])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_MULTI_OUT))
        finally:
            silent_remove(DEF_OUT)

    def testNoOverlap(self):
        with capture_stderr(align_on_col.main, ["-f", NO_OVER_CMP_LIST]) as output:
            self.assertTrue("Problems reading data" in output)
        silent_remove(DEF_OUT)

    def testDupCol(self):
        with capture_stderr(align_on_col.main, ["-f", DUP_COL_CMP_LIST]) as output:
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
            self.assertTrue("Non-unique column" in output)
        silent_remove(DEF_OUT)

    def testNoTimestep(self):
        with capture_stderr(align_on_col.main, ["-f", NO_COL_CMP_LIST]) as output:
            self.assertTrue("Could not find value" in output)
        silent_remove(DEF_OUT)

    def testNoFile(self):
        with capture_stderr(align_on_col.main, ["-f", NO_FILE_CMP_LIST]) as output:
            self.assertTrue("No such file or directory" in output)
