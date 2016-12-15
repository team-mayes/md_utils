# coding=utf-8

"""
Tests for lammps_proc.py.
"""
import os
import unittest
from md_utils.lammps_proc import main, WAT_H_TYPE, WAT_O_TYPE, PROT_O_IDS, H3O_O_TYPE, H3O_H_TYPE
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
import logging

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'


DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'lammps_proc')

# Check catching error
NO_ACTION_INI_PATH = os.path.join(SUB_DATA_DIR, 'hstar_o_gofr_no_action.ini')
INCOMP_INI_PATH = os.path.join(SUB_DATA_DIR, 'lammps_proc_data_incomp.ini')
INVALID_INI = os.path.join(SUB_DATA_DIR, 'lammps_proc_data_invalid.ini')
WRONG_CARB_O_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_wrong_carb_o.ini')
WRONG_HYD_O_TYPE_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_wrong_hyd_o_type.ini')
WRONG_HYD_H_TYPE_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_wrong_hyd_h_type.ini')
WRONG_WAT_O_TYPE_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_wrong_wat_o_type.ini')
WRONG_WAT_H_TYPE_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_wrong_wat_h_type.ini')
EXTRA_HYD_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_extra_hyd_atoms.ini')
HYD_AND_H_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_hyd_and_h.ini')

OH_DIST_INI = os.path.join(SUB_DATA_DIR, 'hydroxyl_oh_dist.ini')
# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(SUB_DATA_DIR, 'glue_sum.csv')
GOOD_OH_DIST_OUT = os.path.join(SUB_DATA_DIR, 'glue_oh_dist_good.csv')

EMPTY_LIST_INI = os.path.join(SUB_DATA_DIR, 'lammps_proc_empty_list.ini')
MISS_DUMP_INI = os.path.join(SUB_DATA_DIR, 'lammps_proc_data_missing_dump.ini')
BAD_DUMP_INI = os.path.join(SUB_DATA_DIR, 'lammps_proc_data_bad_dump.ini')
INCOMP_GOFR_INI_PATH = os.path.join(SUB_DATA_DIR, 'hstar_o_gofr_missing_delta_r.ini')
INCOMP_DUMP_INI_PATH = os.path.join(SUB_DATA_DIR, 'hstar_o_gofr_incomp_dump.ini')
INCOMP_PROT_O_INI = os.path.join(SUB_DATA_DIR, 'lammps_proc_miss_prot_oxys.ini')

HO_GOFR_INI_PATH = os.path.join(SUB_DATA_DIR, 'hstar_o_gofr.ini')
GOOD_HO_GOFR_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_gofr_ho_good.csv')

OO_GOFR_INI_PATH = os.path.join(SUB_DATA_DIR, 'ostar_o_gofr.ini')
GOOD_OO_GOFR_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_gofr_oo_good.csv')

HH_GOFR_INI_PATH = os.path.join(SUB_DATA_DIR, 'hstar_h_gofr.ini')
GOOD_HH_GOFR_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_gofr_hh_good.csv')

OH_GOFR_INI_PATH = os.path.join(SUB_DATA_DIR, 'ostar_h_gofr.ini')
GOOD_OH_GOFR_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_gofr_oh_good.csv')

HO_OO_HH_OH_GOFR_INI = os.path.join(SUB_DATA_DIR, 'ho_oo_hh_oh_gofr.ini')
GOOD_HO_OO_HH_OH_GOFR_OUT = os.path.join(SUB_DATA_DIR, 'glue_gofr_ho_oo_hh_oh_good.csv')

HO_OO_HH_OH_GOFR_INI_MAX_STEPS = os.path.join(SUB_DATA_DIR, 'ho_oo_hh_oh_gofr_max_steps.ini')
GOOD_HO_OO_HH_OH_GOFR_OUT_MAX_STEPS = os.path.join(SUB_DATA_DIR, 'glue_dump_long_gofrs_good.csv')

# noinspection PyUnresolvedReferences
DEF_GOFR_OUT = os.path.join(SUB_DATA_DIR, 'glue_dump_gofrs.csv')
# noinspection PyUnresolvedReferences
DEF_GOFR_INCOMP_OUT = os.path.join(SUB_DATA_DIR, 'glue_dump_incomp_gofrs.csv')
# noinspection PyUnresolvedReferences
DEF_MAX_STEPS_OUT = os.path.join(SUB_DATA_DIR, 'glue_dump_long_gofrs.csv')

HIJ_INI = os.path.join(SUB_DATA_DIR, 'calc_hij.ini')
# noinspection PyUnresolvedReferences
HIJ_OUT = os.path.join(SUB_DATA_DIR, 'glu_prot_deprot_sum.csv')
GOOD_HIJ_OUT = os.path.join(SUB_DATA_DIR, 'glu_prot_deprot_proc_data_good.csv')

WAT_HYD_INI = os.path.join(SUB_DATA_DIR, 'calc_wat_hyd.ini')
GOOD_WAT_HYD_OUT = os.path.join(SUB_DATA_DIR, 'glu_prot_deprot_wat_hyd_good.csv')

HIJ_ARQ_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_arq.ini')
# noinspection PyUnresolvedReferences
HIJ_ARQ_OUT = os.path.join(SUB_DATA_DIR, 'glue_revised_sum.csv')
GOOD_HIJ_ARQ_OUT = os.path.join(SUB_DATA_DIR, 'glue_revised_arq_good.csv')

HIJ_NEW_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_arq_new.ini')
GOOD_HIJ_NEW_OUT = os.path.join(SUB_DATA_DIR, 'glue_revised_new_hij_good.csv')

HIJ_NEW_GLU2_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_glu_arq_new.ini')
HIJ_NEW_GLU2_OUT = os.path.join(SUB_DATA_DIR, 'gluprot10_10no_evb_sum.csv')
GOOD_HIJ_NEW_GLU2_OUT = os.path.join(SUB_DATA_DIR, 'gluprot10_10no_evb_sum_good.csv')

HIJ_NEW_MISS_PARAM_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_arq_new_missing_param.ini')
HIJ_NEW_NONFLOAT_PARAM_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_arq_new_non_float_param.ini')

CALC_GLU_PROPS_INI = os.path.join(SUB_DATA_DIR, 'calc_glu_props.ini')
GOOD_GLU_PROPS_OUT = os.path.join(SUB_DATA_DIR, 'gluprot10_10no_evb_oco_good.csv')

COMBINE_CEC_INI = os.path.join(SUB_DATA_DIR, 'calc_cec_dist.ini')
COMBINE_CEC_OUT = os.path.join(SUB_DATA_DIR, '2.400_320_short_sum.csv')
GOOD_COMBINE_CEC_OUT = os.path.join(SUB_DATA_DIR, '2.400_320_short_sum_good.csv')


good_long_out_msg = 'md_utils/tests/test_data/lammps_proc/glue_dump_long_gofrs.csv\nReached the maximum timesteps ' \
                    'per dumpfile (20). To increase this number, set a larger value for max_timesteps_per_dumpfile. ' \
                    'Continuing program.\nCompleted reading'


class TestLammpsProcDataNoOutput(unittest.TestCase):
    # These tests only check for (hopefully) helpful messages
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoInputFile(self):
        with capture_stderr(main) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)
        with capture_stdout(main) as output:
            self.assertTrue("optional arguments" in output)

    def testInvalidData(self):
        test_input = ["-c", INVALID_INI]
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problem with config vals on key h3o_o_type: invalid literal for int" in output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoAction(self):
        test_input = ["-c", NO_ACTION_INI_PATH]
        with capture_stderr(main, test_input) as output:
            self.assertTrue("No calculations have been requested" in output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testMissDump(self):
        with capture_stderr(main, ["-c", MISS_DUMP_INI]) as output:
            self.assertTrue("No such file or directory" in output)

    def testBadDump(self):
        with capture_stderr(main, ["-c", BAD_DUMP_INI]) as output:
            self.assertTrue("invalid literal for int()" in output)

    def testMissingConfig(self):
        test_input = ["-c", INCOMP_INI_PATH]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Missing config val for key 'water_o_type'" in output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testIncompProtType(self):
        with capture_stderr(main, ["-c", INCOMP_PROT_O_INI]) as output:
            self.assertTrue("WARNING" in output)
            self.assertTrue("Expected to find exactly" in output)

    def testNegGofR(self):
        with capture_stderr(main, ["-c", INCOMP_GOFR_INI_PATH]) as output:
            self.assertTrue("a positive value" in output)

    def testHydAndH(self):
        with capture_stderr(main, ["-c", HYD_AND_H_INI]) as output:
            for expected in [' 3 ', 'Excess proton', H3O_O_TYPE, H3O_H_TYPE]:
                self.assertTrue(expected in output)

    def testExtraHydAtoms(self):
        with capture_stderr(main, ["-c", EXTRA_HYD_INI]) as output:
            for expected in [' 7 ', 'No excess proton', H3O_O_TYPE, H3O_H_TYPE]:
                self.assertTrue(expected in output)

    def testFindNoCarbO(self):
        with capture_stderr(main, ["-c", WRONG_CARB_O_INI]) as output:
            self.assertTrue(PROT_O_IDS in output)

    def testWrongHydH(self):
        with capture_stderr(main, ["-c", WRONG_HYD_H_TYPE_INI]) as output:
            for expected in [' 1 ', 'No excess proton', H3O_O_TYPE, H3O_H_TYPE]:
                self.assertTrue(expected in output)

    def testWrongHydO(self):
        with capture_stderr(main, ["-c", WRONG_HYD_O_TYPE_INI]) as output:
            for expected in [' 3 ', 'No excess proton', H3O_O_TYPE, H3O_H_TYPE]:
                self.assertTrue(expected in output)

    def testFindNoWatO(self):
        with capture_stderr(main, ["-c", WRONG_WAT_O_TYPE_INI]) as output:
            self.assertTrue(WAT_O_TYPE in output)
            self.assertTrue("no such atoms were found" in output)

    def testFindNoWatH(self):
        test_input = ["-c", WRONG_WAT_H_TYPE_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue(WAT_H_TYPE in output)
            self.assertTrue("no such atoms were found" in output)

    def testEmptyList(self):
        test_input = ["-c", EMPTY_LIST_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Found no dump files to process" in output)

    def testMissNewHIJMissingParam(self):
        test_input = ["-c", HIJ_NEW_MISS_PARAM_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Missing input value for key" in output)

    def testMissNewHIJNonfloatParam(self):
        test_input = ["-c", HIJ_NEW_NONFLOAT_PARAM_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Require float inputs for keys" in output)


class TestLammpsProcData(unittest.TestCase):
    def testOHDist(self):
        num = 12
        print(isinstance(num, float))
        try:
            main(["-c", OH_DIST_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OH_DIST_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testMaxTimestepsCalcHIJ(self):
        try:
            with capture_stdout(main, ["-c", HIJ_INI]) as output:
                self.assertTrue("Reached the maximum timesteps" in output)
            self.assertFalse(diff_lines(HIJ_OUT, GOOD_HIJ_OUT))
        finally:
            silent_remove(HIJ_OUT, disable=DISABLE_REMOVE)

    def testMaxTimestepsCalcWatHyd(self):
        try:
            main(["-c", WAT_HYD_INI])
            self.assertFalse(diff_lines(HIJ_OUT, GOOD_WAT_HYD_OUT))
        finally:
            silent_remove(HIJ_OUT, disable=DISABLE_REMOVE)

    def testHIJArq(self):
        # Test calculating the Maupin form
        try:
            test_input = ["-c", HIJ_ARQ_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stderr(main, test_input) as output:
                self.assertTrue("did not have the full list of atom numbers" in output)
            self.assertFalse(diff_lines(HIJ_ARQ_OUT, GOOD_HIJ_ARQ_OUT))
        finally:
            silent_remove(HIJ_ARQ_OUT, disable=DISABLE_REMOVE)

    def testIncompDump(self):
        try:
            with capture_stderr(main, ["-c", INCOMP_DUMP_INI_PATH]) as output:
                self.assertTrue("WARNING" in output)
            self.assertFalse(diff_lines(DEF_GOFR_INCOMP_OUT, GOOD_HO_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_INCOMP_OUT, disable=DISABLE_REMOVE)

    def testHOGofR(self):
        try:
            main(["-c", HO_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_HO_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT, disable=DISABLE_REMOVE)

    def testOOGofR(self):
        try:
            main(["-c", OO_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_OO_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT, disable=DISABLE_REMOVE)

    def testHHGofR(self):
        try:
            main(["-c", HH_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_HH_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT, disable=DISABLE_REMOVE)

    def testOHGofR(self):
        try:
            main(["-c", OH_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_OH_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT, disable=DISABLE_REMOVE)

    def testHO_OO_HH_OHGofR(self):
        try:
            main(["-c", HO_OO_HH_OH_GOFR_INI])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_HO_OO_HH_OH_GOFR_OUT))
        finally:
            silent_remove(DEF_GOFR_OUT, disable=DISABLE_REMOVE)

    def testHO_OO_HH_OHGofR_MaxSteps(self):
        test_input = ["-c", HO_OO_HH_OH_GOFR_INI_MAX_STEPS]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue(good_long_out_msg in output)
            self.assertFalse(diff_lines(DEF_MAX_STEPS_OUT, GOOD_HO_OO_HH_OH_GOFR_OUT_MAX_STEPS))
        finally:
            silent_remove(DEF_MAX_STEPS_OUT, disable=DISABLE_REMOVE)

    def testHIJArqNew(self):
        # Test calculating the Maupin form
        try:
            test_input = ["-c", HIJ_NEW_INI]
            main(test_input)
            self.assertFalse(diff_lines(HIJ_ARQ_OUT, GOOD_HIJ_NEW_OUT))
        finally:
            silent_remove(HIJ_ARQ_OUT, disable=DISABLE_REMOVE)

    def testHIJArqNew2(self):
        # Test calculating the Maupin form
        try:
            test_input = ["-c", HIJ_NEW_GLU2_INI, "-p"]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            # because i've turned off printing, there should be no output
            with capture_stdout(main, test_input) as output:
                self.assertFalse(output)
            self.assertFalse(diff_lines(HIJ_NEW_GLU2_OUT, GOOD_HIJ_NEW_GLU2_OUT))
        finally:
            silent_remove(HIJ_NEW_GLU2_OUT, disable=DISABLE_REMOVE)

    def testCalcProps(self):
        try:
            test_input = ["-c", CALC_GLU_PROPS_INI, "-p"]
            main(test_input)
            self.assertFalse(diff_lines(HIJ_NEW_GLU2_OUT, GOOD_GLU_PROPS_OUT))
        finally:
            silent_remove(HIJ_NEW_GLU2_OUT, disable=DISABLE_REMOVE)

    def testCombineCEC(self):
        try:
            test_input = ["-c", COMBINE_CEC_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stderr(main, test_input) as output:
                self.assertTrue("Did not find 'timestep' value" in output)
            self.assertFalse(diff_lines(COMBINE_CEC_OUT, GOOD_COMBINE_CEC_OUT))
        finally:
            silent_remove(COMBINE_CEC_OUT, disable=DISABLE_REMOVE)
