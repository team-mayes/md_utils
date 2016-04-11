# coding=utf-8

"""
Tests for lammps_proc_data.py.
"""
import os
import unittest

from md_utils import lammps_proc_data
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'


DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'lammps_proc')

NO_ACTION_INI_PATH = os.path.join(SUB_DATA_DIR, 'hstar_o_gofr_no_action.ini')
INCOMP_INI_PATH = os.path.join(SUB_DATA_DIR, 'lammps_proc_data_incomp.ini')
INVALID_INI_PATH = os.path.join(SUB_DATA_DIR, 'lammps_proc_data_invalid.ini')
LONG_INI_PATH = os.path.join(SUB_DATA_DIR, 'lammps_proc_data_long.ini')

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

HIJ_INI_PATH = os.path.join(SUB_DATA_DIR, 'calc_hij.ini')
# noinspection PyUnresolvedReferences
DEF_HIJ_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glu_prot_deprot_proc_data.csv')
GOOD_HIJ_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glu_prot_deprot_proc_data_good.csv')

good_long_out_msg = 'md_utils/tests/test_data/lammps_proc/glue_dump_long_gofrs.csv\nReached the maximum timesteps ' \
                    'per dumpfile (20). To increase this number, set a larger value for max_timesteps_per_dumpfile. ' \
                    'Continuing program.\nCompleted reading dumpfile'


class TestLammpsProcData(unittest.TestCase):
    def testNoInputFile(self):
        with capture_stderr(lammps_proc_data.main) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)
        with capture_stdout(lammps_proc_data.main) as output:
            self.assertTrue("optional arguments" in output)

    def testInvalidData(self):
        with capture_stderr(lammps_proc_data.main, ["-c", INVALID_INI_PATH]) as output:
            self.assertTrue("Problem with default config vals on key h3o_o_type: invalid literal for int" in output)
        with capture_stdout(lammps_proc_data.main, ["-c", INVALID_INI_PATH]) as output:
            self.assertTrue("optional arguments" in output)

    def testNoAction(self):
        with capture_stderr(lammps_proc_data.main, ["-c", NO_ACTION_INI_PATH]) as output:
            self.assertTrue("No calculations have been requested" in output)
        with capture_stdout(lammps_proc_data.main, ["-c", NO_ACTION_INI_PATH]) as output:
            self.assertTrue("optional arguments" in output)

    def testMissDump(self):
        with capture_stderr(lammps_proc_data.main, ["-c", MISS_DUMP_INI]) as output:
            self.assertTrue("No such file or directory" in output)

    def testBadDump(self):
        with capture_stderr(lammps_proc_data.main, ["-c", BAD_DUMP_INI]) as output:
            self.assertTrue("Problems reading data: Unexpected line in file " in output)

    def testMissingConfig(self):
        lammps_proc_data.main(["-c", INCOMP_INI_PATH])
        with capture_stderr(lammps_proc_data.main, ["-c", INCOMP_INI_PATH]) as output:
            self.assertTrue("Input data missing" in output)
        with capture_stdout(lammps_proc_data.main, ["-c", INCOMP_INI_PATH]) as output:
            self.assertTrue("optional arguments" in output)

    def testOHDist(self):
        try:
            lammps_proc_data.main(["-c", OH_DIST_INI_PATH])
            self.assertFalse(diff_lines(DEF_OUT_PATH, GOOD_OH_DIST_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testMaxTimestepsCalcHIJ(self):
        with capture_stdout(lammps_proc_data.main, ["-c", HIJ_INI_PATH]) as output:
            try:
                self.assertTrue("Reached the maximum timesteps" in output)
                self.assertFalse(diff_lines(DEF_HIJ_OUT_PATH, GOOD_HIJ_OUT_PATH))
            finally:
                silent_remove(DEF_HIJ_OUT_PATH)

    def testIncompDump(self):
        try:
            with capture_stderr(lammps_proc_data.main, ["-c", INCOMP_DUMP_INI_PATH]) as output:
                self.assertTrue("WARNING" in output)
            with capture_stdout(lammps_proc_data.main, ["-c", INCOMP_DUMP_INI_PATH]) as output:
                self.assertTrue("Wrote file" in output)
            self.assertFalse(diff_lines(DEF_GOFR_INCOMP_OUT, GOOD_HO_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_INCOMP_OUT)

    def testIncompProtType(self):
        with capture_stderr(lammps_proc_data.main, ["-c", INCOMP_PROT_O_INI]) as output:
            self.assertTrue("WARNING" in output)
            self.assertTrue("Expected to find exactly" in output)

    def testNegGofR(self):
        with capture_stderr(lammps_proc_data.main, ["-c", INCOMP_GOFR_INI_PATH]) as output:
            self.assertTrue("a positive value" in output)

    def testHOGofR(self):
        try:
            lammps_proc_data.main(["-c", HO_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_HO_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT)

    def testOOGofR(self):
        try:
            lammps_proc_data.main(["-c", OO_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_OO_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT)

    def testHHGofR(self):
        try:
            lammps_proc_data.main(["-c", HH_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_HH_GOFR_OUT_PATH))
        finally:
            # silent_remove(DEF_GOFR_OUT)
            pass

    def testOHGofR(self):
        try:
            lammps_proc_data.main(["-c", OH_GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_OH_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT)

    def testHO_OO_HH_OHGofR(self):
        try:
            lammps_proc_data.main(["-c", HO_OO_HH_OH_GOFR_INI])
            self.assertFalse(diff_lines(DEF_GOFR_OUT, GOOD_HO_OO_HH_OH_GOFR_OUT))
        finally:
            silent_remove(DEF_GOFR_OUT)

    def testHO_OO_HH_OHGofR_MaxSteps(self):
        # lammps_proc_data.main(["-c", HO_OO_HH_OH_GOFR_INI_MAX_STEPS])
        try:
            with capture_stdout(lammps_proc_data.main, ["-c", HO_OO_HH_OH_GOFR_INI_MAX_STEPS]) as output:
                self.assertTrue(good_long_out_msg in output)
            self.assertFalse(diff_lines(DEF_MAX_STEPS_OUT, GOOD_HO_OO_HH_OH_GOFR_OUT_MAX_STEPS))
        finally:
            silent_remove(DEF_MAX_STEPS_OUT)
