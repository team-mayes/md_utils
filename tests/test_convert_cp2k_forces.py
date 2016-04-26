# coding=utf-8

"""
Tests for convert_cp2k_forces.py.
"""
import os
import unittest

from md_utils import convert_cp2k_forces
from md_utils.convert_cp2k_forces import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'


# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
CP2K_DATA_DIR = os.path.join(DATA_DIR, 'cp2k_files')

# Input files #

INCOMP_F_LIST = os.path.join(CP2K_DATA_DIR, 'cp2k_force_list_incomp.txt')
F_LIST = os.path.join(CP2K_DATA_DIR, 'cp2k_force_list_good.txt')

# noinspection PyUnresolvedReferences
BAD_F_LIST = os.path.join(CP2K_DATA_DIR, 'cp2k_force_list_bad.txt')

# Output files #

# noinspection PyUnresolvedReferences
DEF_F_LIST_SUM_PATH = os.path.join(CP2K_DATA_DIR, 'force_sums_cp2k_force_list_good.csv')
GOOD_F_LIST_SUM_PATH = os.path.join(CP2K_DATA_DIR, 'force_sums_cp2k_force_list_good_good.csv')
# noinspection PyUnresolvedReferences
DEF_OUT1_PATH = os.path.join(CP2K_DATA_DIR, 'REF_15_2_502000')
# noinspection PyUnresolvedReferences
DEF_OUT2_PATH = os.path.join(CP2K_DATA_DIR, 'REF_20_1_508000')
GOOD_OUT1_PATH = os.path.join(CP2K_DATA_DIR, 'REF_15_2_502000_good')
GOOD_OUT2_PATH = os.path.join(CP2K_DATA_DIR, 'REF_20_1_508000_good')


class TestConvertCP2K(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(main, []) as output:
            self.assertTrue("show this help message" in output)
        with capture_stderr(main, []) as output:
            self.assertTrue("WARNING:  Default file" in output)

    def testMissingFileList(self):
        with capture_stdout(main, ["-l", " "]) as output:
            self.assertTrue("show this help message" in output)
        with capture_stderr(convert_cp2k_forces.main, []) as output:
            self.assertTrue("WARNING:  Default file" in output)

    def testMissingIncompleteFile(self):
        # main(["-l", INCOMP_F_LIST])
        with capture_stderr(convert_cp2k_forces.main, ["-l", INCOMP_F_LIST]) as output:
            self.assertTrue("Check file" in output)
            self.assertTrue("Could not read file" in output)
        with capture_stdout(convert_cp2k_forces.main, ["-l", INCOMP_F_LIST]) as output:
            self.assertTrue("214084      0.957     -0.413      1.283      1.653" in output)
        try:
            self.assertFalse(diff_lines(DEF_OUT1_PATH, GOOD_OUT1_PATH))
        finally:
            silent_remove(DEF_OUT1_PATH)

    def testGoodInput(self):
        with capture_stdout(main, ["-l", F_LIST]) as output:
            self.assertTrue("214084      0.288     -0.413      1.258      1.437" in output)
            self.assertTrue("214084      0.957      0.631      1.283      1.653" in output)
        try:
            self.assertFalse(diff_lines(DEF_F_LIST_SUM_PATH, GOOD_F_LIST_SUM_PATH))
            self.assertFalse(diff_lines(DEF_OUT1_PATH, GOOD_OUT1_PATH))
            self.assertFalse(diff_lines(DEF_OUT2_PATH, GOOD_OUT2_PATH))
        finally:
            silent_remove(DEF_F_LIST_SUM_PATH)
            silent_remove(DEF_OUT1_PATH)
            silent_remove(DEF_OUT2_PATH)

    def testBadDir(self):
        # main(["-d", 'ghost', "-l", F_LIST])
        with capture_stderr(main, ["-d", 'ghost', "-l", F_LIST]) as output:
            self.assertTrue("Cannot find specified output directory" in output)

    def testNoSuchOption(self):
        # main(["-@", F_LIST])
        with capture_stderr(main, ["-@", F_LIST]) as output:
            self.assertTrue("unrecognized argument" in output)
            self.assertTrue(F_LIST in output)

    def testBadForceFile(self):
        # main(["-l", BAD_F_LIST])
        with capture_stderr(main, ["-l", BAD_F_LIST]) as output:
            self.assertTrue("WARNING:  Did not find the expected four force values" in output)
            self.assertTrue("Check file: " in output)
            self.assertTrue("end of file without encountering a third 'SUM OF ATOMIC FORCES' section" in output)
            self.assertTrue("WARNING:  Did not find six expected values" in output)
            self.assertTrue("WARNING:  No valid cp2k force output files were read" in output)
