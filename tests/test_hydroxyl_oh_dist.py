# coding=utf-8

"""
Tests for hydroxyl_oh_dist.py.
"""
import os
import unittest

from md_utils import hydroxyl_oh_dist
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'


DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'lammps_proc')
INI_PATH = os.path.join(SUB_DATA_DIR, 'hydroxyl_oh_dist.ini')
INCOMP_INI_PATH = os.path.join(SUB_DATA_DIR, 'hyd_oh_dis_incomp.ini')
DEF_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_oh_dist.csv')
GOOD_OUT_PATH = os.path.join(SUB_DATA_DIR, 'glue_oh_dist_good.csv')

class TestHydroxylOHDist(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(hydroxyl_oh_dist.main,[]) as output:
            self.assertTrue("usage:" in output)
        with capture_stderr(hydroxyl_oh_dist.main,[]) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)
    def testOHDist(self):
        try:
            hydroxyl_oh_dist.main(["-c", INI_PATH])
            self.assertFalse(diff_lines(DEF_OUT_PATH, GOOD_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)
    def testMissingConfig(self):
        with capture_stderr(hydroxyl_oh_dist.main,["-c", INCOMP_INI_PATH]) as output:
            self.assertTrue("Input data missing" in output)
        with capture_stdout(hydroxyl_oh_dist.main,["-c", INCOMP_INI_PATH]) as output:
            self.assertTrue("optional arguments" in output)

