# coding=utf-8

"""
Tests for evb_get_info.py.
Also, test diff_lines
"""
import os
import unittest

from md_utils.evb_get_info import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'


# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'evb_info')

# Input files #

INCOMP_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_missing_data.ini')
BAD_PATH_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_path_path.ini')

CI_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info.ini')
# noinspection PyUnresolvedReferences
DEF_CI_OUT1 = os.path.join(SUB_DATA_DIR, '1.500_20c_short_ci_sq.csv')
GOOD_CI_OUT1 = os.path.join(SUB_DATA_DIR, '1.500_20c_short_ci_sq_good.csv')
# noinspection PyUnresolvedReferences
DEF_CI_OUT2 = os.path.join(SUB_DATA_DIR, '2.000_20c_short_ci_sq.csv')
GOOD_CI_OUT2 = os.path.join(SUB_DATA_DIR, '2.000_20c_short_ci_sq_good.csv')
BAD_CI_OUT2 = os.path.join(SUB_DATA_DIR, '2.000_20c_short_ci_sq_bad.csv')

CI_SUBSET_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_subset.ini')
# noinspection PyUnresolvedReferences
DEF_CI_SUBSET_OUT = os.path.join(SUB_DATA_DIR, '1.500_20c_short_ci_sq_ts.csv')
GOOD_CI_SUBSET_OUT = os.path.join(SUB_DATA_DIR, '1.500_20c_short_ci_sq_ts_good.csv')

CI_ONE_STATE_INI = os.path.join(SUB_DATA_DIR, 'serca_evb_get_info.ini')
CI_ONE_STATE_EACH_FILE_INI = os.path.join(SUB_DATA_DIR, 'serca_evb_get_info_per_file.ini')
# noinspection PyUnresolvedReferences
DEF_ONE_STATE_OUT = os.path.join(SUB_DATA_DIR, '0_3_ci_sq.csv')
GOOD_ONE_STATE_OUT = os.path.join(SUB_DATA_DIR, '0_3_ci_sq_good.csv')
# noinspection PyUnresolvedReferences
DEF_ONE_STATE_OUT2 = os.path.join(SUB_DATA_DIR, '31_3_ci_sq.csv')
GOOD_ONE_STATE_OUT2 = os.path.join(SUB_DATA_DIR, '31_3_ci_sq_good.csv')
# noinspection PyUnresolvedReferences
DEF_LIST_OUT = os.path.join(SUB_DATA_DIR, 'serca_evb_list_ci_sq.csv')
GOOD_LIST_OUT = os.path.join(SUB_DATA_DIR, 'serca_evb_list_ci_sq_good.csv')


class TestEVBGetInfo(unittest.TestCase):

    def testNoIni(self):
        with capture_stdout(main, []) as output:
            self.assertTrue("usage:" in output)
        with capture_stderr(main, []) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)

    def testMissingInfo(self):
        with capture_stderr(main, ["-c", INCOMP_INI]) as output:
            self.assertTrue("Input data missing" in output)
        with capture_stdout(main, ["-c", INCOMP_INI]) as output:
            self.assertTrue("optional arguments" in output)

    def testBadPath(self):
        with capture_stderr(main, ["-c", BAD_PATH_INI]) as output:
            self.assertTrue("No such file or directory" in output)

    def testCiInfo(self):
        try:
            main(["-c", CI_INI])
            self.assertFalse(diff_lines(DEF_CI_OUT1, GOOD_CI_OUT1))
            # for debugging:
            # with open(DEF_CI_OUT2) as f:
            #     with open(GOOD_CI_OUT2) as g:
            #         for line, g_line in zip(f, g):
            #             if line.strip() != g_line.strip():
            #                 print(line.strip() == g_line.strip(), line.strip(), g_line.strip())
            #                 print(line.strip())
            #                 print(g_line.strip())
            self.assertFalse(diff_lines(DEF_CI_OUT2, GOOD_CI_OUT2))
        finally:
            silent_remove(DEF_CI_OUT1)
            silent_remove(DEF_CI_OUT2)

    def testSubsetCiInfo(self):
        with capture_stderr(main, ["-c", CI_SUBSET_INI]) as output:
            self.assertTrue("found no data from" in output)
            self.assertFalse(diff_lines(DEF_CI_SUBSET_OUT, GOOD_CI_SUBSET_OUT))
            silent_remove(DEF_CI_OUT1)
            silent_remove(DEF_CI_OUT2)

    def testOneStateCiInfo(self):
        """
        Make sure can handle input that only has one state (such steps have a vector instead of a matrix)
        and does not skip them
        Also, check that properly reads to make a summary file
        """
        try:
            main(["-c", CI_ONE_STATE_INI])
            self.assertFalse(diff_lines(DEF_LIST_OUT, GOOD_LIST_OUT))
        finally:
            silent_remove(DEF_LIST_OUT)

    def testOneStateEachFileCiInfo(self):
        """
        Make sure can handle input that only has one state (such steps have a vector instead of a matrix)
        this time, printing a separate output for each file
        And, skip one-state-steps
        """
        try:
            main(["-c", CI_ONE_STATE_EACH_FILE_INI])
            self.assertFalse(diff_lines(DEF_ONE_STATE_OUT, GOOD_ONE_STATE_OUT))
            self.assertFalse(diff_lines(DEF_ONE_STATE_OUT2, GOOD_ONE_STATE_OUT2))
        finally:
            silent_remove(DEF_ONE_STATE_OUT)
            silent_remove(DEF_ONE_STATE_OUT2)


class TestEVBGetInfoDiffLines(unittest.TestCase):
    def testCiInfo(self):
        try:
            main(["-c", CI_INI])
            self.assertFalse(diff_lines(DEF_CI_OUT1, GOOD_CI_OUT1))
            self.assertTrue(diff_lines(DEF_CI_OUT2, BAD_CI_OUT2))
            self.assertFalse(diff_lines(DEF_CI_OUT2, GOOD_CI_OUT2))
        finally:
            silent_remove(DEF_CI_OUT1)
            silent_remove(DEF_CI_OUT2)