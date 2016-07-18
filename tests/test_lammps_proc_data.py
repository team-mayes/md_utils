# coding=utf-8

"""
Tests for lammps_proc_data.py.
"""
import os
import unittest

from md_utils.lammps_proc_data import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'


DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'lammps_proc')

# Check catching error
NO_ACTION_INI_PATH = os.path.join(SUB_DATA_DIR, 'hstar_o_gofr_no_action.ini')
INCOMP_INI_PATH = os.path.join(SUB_DATA_DIR, 'lammps_proc_data_incomp.ini')
INVALID_INI = os.path.join(SUB_DATA_DIR, 'lammps_proc_data_invalid.ini')
WRONG_WAT_TYPE_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_wrong_wat_type.ini')

OH_DIST_INI_PATH = os.path.join(SUB_DATA_DIR, 'hydroxyl_oh_dist.ini')
# noinspection PyUnresolvedReferences
DEF_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_proc_data.csv')
GOOD_OH_DIST_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_oh_dist_good.csv')

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
HIJ_OUT = os.path.join(SUB_DATA_DIR, 'glu_prot_deprot_proc_data.csv')
GOOD_HIJ_OUT = os.path.join(SUB_DATA_DIR, 'glu_prot_deprot_proc_data_good.csv')

HIJ_ALT_INI = os.path.join(SUB_DATA_DIR, 'calc_hij_alt.ini')
# noinspection PyUnresolvedReferences
HIJ_ALT_OUT = os.path.join(SUB_DATA_DIR, '0.875_20c_100ps_reorder_short_proc_data.csv')
GOOD_HIJ_ALT_OUT = os.path.join(SUB_DATA_DIR, '0.875_20c_100ps_reorder_short_good.csv')

good_long_out_msg = 'md_utils/tests/test_data/lammps_proc/glue_dump_long_gofrs.csv\nReached the maximum timesteps ' \
                    'per dumpfile (20). To increase this number, set a larger value for max_timesteps_per_dumpfile. ' \
                    'Continuing program.\nCompleted reading dumpfile'


class TestLammpsProcDataNoOutput(unittest.TestCase):
    # These tests only check for bad input
    def testNoInputFile(self):
        with capture_stderr(main) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)
        with capture_stdout(main) as output:
            self.assertTrue("optional arguments" in output)

    def testInvalidData(self):
        # main(["-c", INVALID_INI])
        with capture_stderr(main, ["-c", INVALID_INI]) as output:
            self.assertTrue("Problem with config vals on key h3o_o_type: invalid literal for int" in output)
        with capture_stdout(main, ["-c", INVALID_INI]) as output:
            self.assertTrue("optional arguments" in output)

    def testNoAction(self):
        with capture_stderr(main, ["-c", NO_ACTION_INI_PATH]) as output:
            self.assertTrue("No calculations have been requested" in output)
        with capture_stdout(main, ["-c", NO_ACTION_INI_PATH]) as output:
            self.assertTrue("optional arguments" in output)

    def testMissDump(self):
        with capture_stderr(main, ["-c", MISS_DUMP_INI]) as output:
            self.assertTrue("No such file or directory" in output)

    def testBadDump(self):
        # main(["-c", BAD_DUMP_INI])
        with capture_stderr(main, ["-c", BAD_DUMP_INI]) as output:
            self.assertTrue("invalid literal for int()" in output)

    def testMissingConfig(self):
        with capture_stderr(main, ["-c", INCOMP_INI_PATH]) as output:
            self.assertTrue("Input data missing" in output)
        with capture_stdout(main, ["-c", INCOMP_INI_PATH]) as output:
            self.assertTrue("optional arguments" in output)

    def testIncompProtType(self):
        # main(["-c", INCOMP_PROT_O_INI])
        with capture_stderr(main, ["-c", INCOMP_PROT_O_INI]) as output:
            self.assertTrue("WARNING" in output)
            self.assertTrue("Expected to find exactly" in output)

    def testNegGofR(self):
        with capture_stderr(main, ["-c", INCOMP_GOFR_INI_PATH]) as output:
            self.assertTrue("a positive value" in output)

    def testFindNoWater(self):
        with capture_stderr(main, ["-c", WRONG_WAT_TYPE_INI]) as output:
            self.assertTrue("no such atoms were found" in output)


class TestLammpsProcData(unittest.TestCase):
    def testOHDist(self):
        try:
            main(["-c", OH_DIST_INI_PATH])
            self.assertFalse(diff_lines(DEF_OUT_PATH, GOOD_OH_DIST_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)
            # pass

    def testMaxTimestepsCalcHIJ(self):
        # main(["-c", HIJ_INI])
        try:
            with capture_stdout(main, ["-c", HIJ_INI]) as output:
                self.assertTrue("Reached the maximum timesteps" in output)
            self.assertFalse(diff_lines(HIJ_OUT, GOOD_HIJ_OUT))
        finally:
            silent_remove(HIJ_OUT)
            # pass

    def testHIJAlt(self):
        try:
            with capture_stderr(main, ["-c", HIJ_ALT_INI]) as output:
                self.assertTrue("did not have the full list of atom numbers" in output)
            # main(["-c", HIJ_ALT_INI])
            self.assertFalse(diff_lines(HIJ_ALT_OUT, GOOD_HIJ_ALT_OUT))
        finally:
            silent_remove(HIJ_ALT_OUT)

    def testIncompDump(self):
        try:
            with capture_stderr(main, ["-c", INCOMP_DUMP_INI_PATH]) as output:
                self.assertTrue("WARNING" in output)
            self.assertFalse(diff_lines(DEF_GOFR_INCOMP_OUT, GOOD_HO_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_INCOMP_OUT)
            # pass

    def testHOGofR(self):
        try:
            main(["-c", HO_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_HO_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT)
            # pass

    def testOOGofR(self):
        try:
            main(["-c", OO_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_OO_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT)
            # pass

    def testHHGofR(self):
        try:
            main(["-c", HH_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_HH_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT)
            # pass

    def testOHGofR(self):
        try:
            main(["-c", OH_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_OH_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT)
            # pass

    def testHO_OO_HH_OHGofR(self):
        try:
            main(["-c", HO_OO_HH_OH_GOFR_INI])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_HO_OO_HH_OH_GOFR_OUT))
        finally:
            silent_remove(DEF_GOFR_OUT)
            # pass

    def testHO_OO_HH_OHGofR_MaxSteps(self):
        # main(["-c", HO_OO_HH_OH_GOFR_INI_MAX_STEPS])
        try:
            with capture_stdout(main, ["-c", HO_OO_HH_OH_GOFR_INI_MAX_STEPS]) as output:
                self.assertTrue(good_long_out_msg in output)
            self.assertFalse(diff_lines(DEF_MAX_STEPS_OUT, GOOD_HO_OO_HH_OH_GOFR_OUT_MAX_STEPS))
        finally:
            silent_remove(DEF_MAX_STEPS_OUT)
            # pass
