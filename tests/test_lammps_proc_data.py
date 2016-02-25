# coding=utf-8

"""
Tests for hydroxyl_oh_dist.py.
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
OH_DIST_INI_PATH = os.path.join(SUB_DATA_DIR, 'hydroxyl_oh_dist.ini')
DEF_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_dump_proc_data.csv')
GOOD_OH_DIST_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_oh_dist_good.csv')
INCOMP_GOFR_INI_PATH = os.path.join(SUB_DATA_DIR, 'hstar_o_gofr_missing_delta_r.ini')
INCOMP_DUMP_INI_PATH = os.path.join(SUB_DATA_DIR, 'hstar_o_gofr_incomp_dump.ini')
GOFR_INI_PATH = os.path.join(SUB_DATA_DIR, 'hstar_o_gofr.ini')
GOOD_GOFR_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_gofr_ho_good.csv')
DEF_GOFR_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_gofr_ho.csv')
DEF_GOFR_INCOMP_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_incomp_gofr_ho.csv')
HIJ_INI_PATH = os.path.join(SUB_DATA_DIR, 'calc_hij.ini')
DEF_HIJ_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glu_prot_deprot_proc_data.csv')
GOOD_HIJ_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glu_prot_deprot_proc_data_good.csv')

class TestLammpsProcData(unittest.TestCase):
    def testNoAction(self):
        with capture_stderr(lammps_proc_data.main,["-c", NO_ACTION_INI_PATH]) as output:
            self.assertTrue("No calculations have been requested" in output)
        with capture_stdout(lammps_proc_data.main,["-c", NO_ACTION_INI_PATH]) as output:
            self.assertTrue("optional arguments" in output)
    def testNoIni(self):
        with capture_stdout(lammps_proc_data.main,[]) as output:
            self.assertTrue("usage:" in output)
        with capture_stderr(lammps_proc_data.main,[]) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)
    def testMissingConfig(self):
        with capture_stderr(lammps_proc_data.main,["-c", INCOMP_INI_PATH]) as output:
            self.assertTrue("Input data missing" in output)
        with capture_stdout(lammps_proc_data.main,["-c", INCOMP_INI_PATH]) as output:
            self.assertTrue("optional arguments" in output)
    def testOHDist(self):
        try:
            lammps_proc_data.main(["-c", OH_DIST_INI_PATH])
            self.assertFalse(diff_lines(DEF_OUT_PATH, GOOD_OH_DIST_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)
    def testMaxTimestepsCalcHIJ(self):
        with capture_stderr(lammps_proc_data.main,["-c", HIJ_INI_PATH]) as output:
            try:
                self.assertTrue("more than the maximum" in output)
                self.assertFalse(diff_lines(DEF_HIJ_OUT_PATH, GOOD_HIJ_OUT_PATH))
            finally:
                silent_remove(DEF_HIJ_OUT_PATH)
    def testIncompDump(self):
        try:
            with capture_stderr(lammps_proc_data.main,["-c", INCOMP_DUMP_INI_PATH]) as output:
                self.assertTrue("WARNING" in output)
            with capture_stdout(lammps_proc_data.main,["-c", INCOMP_DUMP_INI_PATH]) as output:
                self.assertTrue("Wrote file" in output)
            self.assertFalse(diff_lines(DEF_GOFR_INCOMP_OUT_PATH, GOOD_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_INCOMP_OUT_PATH)
    def testNegGofR(self):
        with capture_stderr(lammps_proc_data.main,["-c", INCOMP_GOFR_INI_PATH]) as output:
            self.assertTrue("a positive value" in output)
    def testHOGofR(self):
        try:
            lammps_proc_data.main(["-c", GOFR_INI_PATH])
            self.assertFalse(diff_lines(DEF_GOFR_OUT_PATH, GOOD_GOFR_OUT_PATH))
        finally:
            silent_remove(DEF_GOFR_OUT_PATH)
