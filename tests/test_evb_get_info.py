# coding=utf-8

"""
Tests for evb_get_info.py.
Also, test diff_lines
"""
import os
import unittest
from md_utils.evb_get_info import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
import logging

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'


# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'evb_info')

# Input files paired with output #

INCOMP_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_missing_data.ini')
BAD_PATH_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_bad_path.ini')
NO_PATH_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_no_path.ini')

CI_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info.ini')
# noinspection PyUnresolvedReferences
DEF_CI_OUT1 = os.path.join(SUB_DATA_DIR, '1.500_20c_short_evb_info.csv')
GOOD_CI_OUT1 = os.path.join(SUB_DATA_DIR, '1.500_20c_short_ci_sq_good.csv')
# noinspection PyUnresolvedReferences
DEF_CI_OUT2 = os.path.join(SUB_DATA_DIR, '2.000_20c_short_evb_info.csv')
GOOD_CI_OUT2 = os.path.join(SUB_DATA_DIR, '2.000_20c_short_ci_sq_good.csv')
BAD_CI_OUT2 = os.path.join(SUB_DATA_DIR, '2.000_20c_short_ci_sq_bad.csv')

CI_SUBSET_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_subset.ini')
# noinspection PyUnresolvedReferences
DEF_CI_SUBSET_OUT = os.path.join(SUB_DATA_DIR, '1.500_20c_short_ci_sq_ts.csv')
GOOD_CI_SUBSET_OUT = os.path.join(SUB_DATA_DIR, '1.500_20c_short_ci_sq_ts_good.csv')

CI_ONE_STATE_INI = os.path.join(SUB_DATA_DIR, 'serca_evb_get_info.ini')
CI_ONE_STATE_EACH_FILE_INI = os.path.join(SUB_DATA_DIR, 'serca_evb_get_info_per_file.ini')
# noinspection PyUnresolvedReferences
DEF_ONE_STATE_OUT = os.path.join(SUB_DATA_DIR, '0_3_evb_info.csv')
GOOD_ONE_STATE_OUT = os.path.join(SUB_DATA_DIR, '0_3_ci_sq_good.csv')
# noinspection PyUnresolvedReferences
DEF_ONE_STATE_OUT2 = os.path.join(SUB_DATA_DIR, '31_3_evb_info.csv')
GOOD_ONE_STATE_OUT2 = os.path.join(SUB_DATA_DIR, '31_3_ci_sq_good.csv')
# noinspection PyUnresolvedReferences
DEF_LIST_OUT = os.path.join(SUB_DATA_DIR, 'serca_evb_list_evb_info.csv')
GOOD_LIST_OUT = os.path.join(SUB_DATA_DIR, 'serca_evb_list_ci_sq_good.csv')

BAD_KEY_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_bad_key.ini')
BAD_EVB_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_bad_evb.ini')
NO_SUCH_EVB_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_no_such_evb.ini')

KEY_PROPS_INI = os.path.join(SUB_DATA_DIR, 'evb_get_key_props.ini')
KEY_PROPS_OUT = os.path.join(SUB_DATA_DIR, 'evb_list_evb_info.csv')
GOOD_KEY_PROPS_OUT = os.path.join(SUB_DATA_DIR, 'evb_list_evb_info_good.csv')

WATER_MOL_INI = os.path.join(SUB_DATA_DIR, 'evb_get_water_mol.ini')
GOOD_WATER_MOL_OUT1 = os.path.join(SUB_DATA_DIR, '1.500_20c_short_wat_mols_good.csv')
GOOD_WATER_MOL_OUT2 = os.path.join(SUB_DATA_DIR, '2.000_20c_short_wat_mols_good.csv')

WATER_MOL_COMB_INI = os.path.join(SUB_DATA_DIR, 'evb_get_water_mol_combine.ini')
WATER_MOL_COMB_OUT = os.path.join(SUB_DATA_DIR, 'evb_list_evb_info.csv')
GOOD_WATER_MOL_COMB_OUT = os.path.join(SUB_DATA_DIR, 'evb_list_wat_mols_good.csv')

REL_ENE_INI = os.path.join(SUB_DATA_DIR, 'evb_rel_ene.ini')
REL_ENE_OUT = os.path.join(SUB_DATA_DIR, 'evb_ene_list_evb_info.csv')
GOOD_REL_ENE_OUT = os.path.join(SUB_DATA_DIR, 'evb_ene_list_rel_e_good.csv')
REL_ENE_INI2 = os.path.join(SUB_DATA_DIR, 'evb_rel_ene2.ini')
REL_ENE_OUT2 = os.path.join(SUB_DATA_DIR, 'evb_ene_list2_evb_info.csv')
GOOD_REL_ENE_OUT2 = os.path.join(SUB_DATA_DIR, 'evb_ene_list2_evb_info_good.csv')

DECOMP_ENE_INI = os.path.join(SUB_DATA_DIR, 'evb_decomp_ene.ini')
GOOD_DECOMP_ENE_OUT = os.path.join(SUB_DATA_DIR, 'evb_ene_list2_ene_info_good.csv')

RMSD_ENE_INI = os.path.join(SUB_DATA_DIR, 'evb_rel_ene_rmsd.ini')
GOOD_RMSD_ENE_OUT = os.path.join(SUB_DATA_DIR, 'evb_ene_list2_rmsd_good.csv')

MAX_STEPS_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_max_steps.ini')
MAX_STEPS_OUT = os.path.join(SUB_DATA_DIR, '2.000_20c_short_evb_info.csv')
GOOD_MAX_STEPS_OUT = os.path.join(SUB_DATA_DIR, '2.000_20c_max_steps_good.csv')

MULTI_SUM_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_multi_sum.ini')
MULTI_SUM_OUT = os.path.join(SUB_DATA_DIR, 'gluprot1min_evb_evb_info.csv')
GOOD_MULTI_SUM_OUT = os.path.join(SUB_DATA_DIR, 'gluprot1min_evb_evb_info_good.csv')

REPEATED_EVB_STEP_INI = os.path.join(SUB_DATA_DIR, 'evb_get_info_repeated_timestep.ini')
REPEATED_EVB_STEP_OUT = os.path.join(SUB_DATA_DIR, 'gluprot13_-6_evb_info.csv')
GOOD_REPEATED_EVB_STEP_OUT = os.path.join(SUB_DATA_DIR, 'gluprot13_-6_evb_info_good.csv')


class TestEVBGetInfoNoOutput(unittest.TestCase):
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoIni(self):
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("usage:" in output)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)

    def testMissingInfo(self):
        test_input = ["-c", INCOMP_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Missing config val for key 'prot_res_mol_id'" in output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testBadPath(self):
        test_input = ["-c", BAD_PATH_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("No such file or directory:" in output)

    def testNoPath(self):
        test_input = ["-c", NO_PATH_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Found no evb file names" in output)

    def testBadKeyword(self):
        with capture_stderr(main, ["-c", BAD_KEY_INI]) as output:
            self.assertTrue("Unexpected key" in output)

    def testBadEVB(self):
        with capture_stderr(main, ["-c", BAD_EVB_INI]) as output:
            self.assertTrue("Problems reading data" in output)

    def testNoSuchEVB(self):
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
            silent_remove(DEF_CI_OUT1, disable=DISABLE_REMOVE)
            silent_remove(DEF_CI_OUT2, disable=DISABLE_REMOVE)

    def testSubsetCiInfo(self):
        with capture_stderr(main, ["-c", CI_SUBSET_INI]) as output:
            self.assertTrue("found no data from" in output)
            self.assertFalse(diff_lines(DEF_CI_SUBSET_OUT, GOOD_CI_SUBSET_OUT))
            silent_remove(DEF_CI_SUBSET_OUT, disable=DISABLE_REMOVE)
            silent_remove(DEF_CI_OUT1, disable=DISABLE_REMOVE)
            silent_remove(DEF_CI_OUT2, disable=DISABLE_REMOVE)

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
            silent_remove(DEF_LIST_OUT, disable=DISABLE_REMOVE)

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
            silent_remove(DEF_ONE_STATE_OUT, disable=DISABLE_REMOVE)
            silent_remove(DEF_ONE_STATE_OUT2, disable=DISABLE_REMOVE)

    def testKeyProps(self):
        try:
            main(["-c", KEY_PROPS_INI])
            self.assertFalse(diff_lines(KEY_PROPS_OUT, GOOD_KEY_PROPS_OUT))
        finally:
            silent_remove(KEY_PROPS_OUT, disable=DISABLE_REMOVE)

    def testWaterMol(self):
        try:
            main(["-c", WATER_MOL_INI, "-p"])
            self.assertFalse(diff_lines(DEF_CI_OUT1, GOOD_WATER_MOL_OUT1))
            self.assertFalse(diff_lines(DEF_CI_OUT2, GOOD_WATER_MOL_OUT2))
        finally:
            silent_remove(DEF_CI_OUT1, disable=DISABLE_REMOVE)
            silent_remove(DEF_CI_OUT2, disable=DISABLE_REMOVE)

    def testWaterMolCombine(self):
        # Should skip the timestep with only 1 state
        try:
            main(["-c", WATER_MOL_COMB_INI, "-p"])
            self.assertFalse(diff_lines(WATER_MOL_COMB_OUT, GOOD_WATER_MOL_COMB_OUT))
        finally:
            silent_remove(WATER_MOL_COMB_OUT, disable=DISABLE_REMOVE)

    def testRelEnergy(self):
        # calculates relative energy
        try:
            main(["-c", REL_ENE_INI, "-p"])
            print(REL_ENE_OUT)
            print(GOOD_REL_ENE_OUT)
            self.assertFalse(diff_lines(REL_ENE_OUT, GOOD_REL_ENE_OUT))
        finally:
            silent_remove(REL_ENE_OUT, disable=DISABLE_REMOVE)

    def testRelEnergyMissingInfo(self):
        # Check that prints "nan" instead of printing a stack trace (uncaught error)
        try:
            main(["-c", REL_ENE_INI2, "-p"])
            print(REL_ENE_OUT2)
            print(GOOD_REL_ENE_OUT2)
            self.assertFalse(diff_lines(REL_ENE_OUT2, GOOD_REL_ENE_OUT2))
        finally:
            silent_remove(REL_ENE_OUT2, disable=DISABLE_REMOVE)

    def testDecomposedEnergyInfo(self):
        try:
            main(["-c", DECOMP_ENE_INI, "-p"])
            self.assertFalse(diff_lines(REL_ENE_OUT2, GOOD_DECOMP_ENE_OUT))
        finally:
            silent_remove(REL_ENE_OUT2, disable=DISABLE_REMOVE)

    def testRMSDEnergy(self):
        try:
            test_input = ["-c", RMSD_ENE_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("23.760125" in output)
            print(REL_ENE_OUT2)
            print(GOOD_RMSD_ENE_OUT)
            self.assertFalse(diff_lines(REL_ENE_OUT2, GOOD_RMSD_ENE_OUT))
        finally:
            silent_remove(REL_ENE_OUT2, disable=DISABLE_REMOVE)

    def testMaxSteps(self):
        try:
            test_input = ["-c", MAX_STEPS_INI]
            main(test_input)
            self.assertFalse(diff_lines(MAX_STEPS_OUT, GOOD_MAX_STEPS_OUT))
        finally:
            silent_remove(MAX_STEPS_OUT, disable=DISABLE_REMOVE)

    def testMultiFileSum(self):
        try:
            test_input = ["-c", MULTI_SUM_INI]
            silent_remove(MULTI_SUM_OUT)
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stderr(main, test_input) as output:
                self.assertTrue("setting 'print_output_file_list' to 'True'" in output)
            self.assertFalse(diff_lines(MULTI_SUM_OUT, GOOD_MULTI_SUM_OUT))
        finally:
            silent_remove(MULTI_SUM_OUT, disable=DISABLE_REMOVE)

    def testRepeatedTimestep(self):
        try:
            test_input = ["-c", REPEATED_EVB_STEP_INI]
            main(test_input)
            self.assertFalse(diff_lines(REPEATED_EVB_STEP_OUT, GOOD_REPEATED_EVB_STEP_OUT))
        finally:
            silent_remove(REPEATED_EVB_STEP_OUT, disable=DISABLE_REMOVE)
