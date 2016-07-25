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

# Input files paired with output #

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

BAD_KEY_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_bad_key.ini')
BAD_EVB_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_bad_evb.ini')
NO_SUCH_EVB_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_no_such_evb.ini')

KEY_PROPS_INI = os.path.join(SUB_DATA_DIR, 'evb_get_key_props.ini')
KEY_PROPS_OUT = os.path.join(SUB_DATA_DIR, 'evb_list_evb_info.csv')
GOOD_KEY_PROPS_OUT = os.path.join(SUB_DATA_DIR, 'evb_list_evb_info_good.csv')

WATER_MOL_INI = os.path.join(SUB_DATA_DIR, 'evb_get_water_mol.ini')
WATER_MOL_OUT1 = os.path.join(SUB_DATA_DIR, '1.500_20c_short_wat_mols.csv')
GOOD_WATER_MOL_OUT1 = os.path.join(SUB_DATA_DIR, '1.500_20c_short_wat_mols_good.csv')
WATER_MOL_OUT2 = os.path.join(SUB_DATA_DIR, '2.000_20c_short_wat_mols.csv')
GOOD_WATER_MOL_OUT2 = os.path.join(SUB_DATA_DIR, '2.000_20c_short_wat_mols_good.csv')

WATER_MOL_COMB_INI = os.path.join(SUB_DATA_DIR, 'evb_get_water_mol_combine.ini')
WATER_MOL_COMB_OUT = os.path.join(SUB_DATA_DIR, 'evb_list_wat_mols.csv')
GOOD_WATER_MOL_COMB_OUT = os.path.join(SUB_DATA_DIR, 'evb_list_wat_mols_good.csv')


class TestEVBGetInfoNoOutput(unittest.TestCase):
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
        main(["-c", BAD_PATH_INI])
        with capture_stderr(main, ["-c", BAD_PATH_INI]) as output:
            self.assertTrue("Found no evb file names to read" in output)

    def testBadKeyword(self):
        # main(["-c", BAD_KEY_INI])
        with capture_stderr(main, ["-c", BAD_KEY_INI]) as output:
            self.assertTrue("Unexpected key" in output)

    def testBadEVB(self):
        # main(["-c", BAD_EVB_INI])
        with capture_stderr(main, ["-c", BAD_EVB_INI]) as output:
            self.assertTrue("Problems reading data" in output)

    def testNoSuchEVB(self):
        # main(["-c", NO_SUCH_EVB_INI])
        with capture_stderr(main, ["-c", NO_SUCH_EVB_INI]) as output:
            self.assertTrue("No such file or directory" in output)


class TestEVBGetInfo(unittest.TestCase):
    def testCiInfo(self):
        try:
            main(["-c", CI_INI])
            self.assertFalse(diff_lines(DEF_CI_OUT1, GOOD_CI_OUT1))
            self.assertEquals(1, len(diff_lines(DEF_CI_OUT2, BAD_CI_OUT2)))
            self.assertFalse(diff_lines(DEF_CI_OUT2, GOOD_CI_OUT2))
        finally:
            silent_remove(DEF_CI_OUT1)
            silent_remove(DEF_CI_OUT2)
            # pass

    def testSubsetCiInfo(self):
        with capture_stderr(main, ["-c", CI_SUBSET_INI]) as output:
            self.assertTrue("found no data from" in output)
            self.assertFalse(diff_lines(DEF_CI_SUBSET_OUT, GOOD_CI_SUBSET_OUT))
            silent_remove(DEF_CI_SUBSET_OUT)
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
            # pass

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
            # pass

    def testKeyProps(self):
        try:
            main(["-c", KEY_PROPS_INI])
            self.assertFalse(diff_lines(KEY_PROPS_OUT, GOOD_KEY_PROPS_OUT))
        finally:
            silent_remove(KEY_PROPS_OUT)
            # pass

    def testWaterMol(self):
        try:
            main(["-c", WATER_MOL_INI])
            self.assertFalse(diff_lines(WATER_MOL_OUT1, GOOD_WATER_MOL_OUT1))
            self.assertFalse(diff_lines(WATER_MOL_OUT2, GOOD_WATER_MOL_OUT2))
        finally:
            silent_remove(WATER_MOL_OUT1)
            silent_remove(WATER_MOL_OUT2)
            # pass

    def testWaterMolCombine(self):
        # Should skip the timestep with only 1 state
        try:
            main(["-c", WATER_MOL_COMB_INI])
            self.assertFalse(diff_lines(WATER_MOL_COMB_OUT, GOOD_WATER_MOL_COMB_OUT))
        finally:
            silent_remove(WATER_MOL_COMB_OUT)
            # pass
