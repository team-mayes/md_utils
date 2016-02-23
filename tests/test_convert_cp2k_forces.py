# coding=utf-8

"""
Tests for convert_cp2k_forces.py.
"""
import os
import unittest

from md_utils import convert_cp2k_forces
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
CP2K_DATA_DIR = os.path.join(DATA_DIR, 'cp2k_files')
FLIST_PATH = os.path.join(CP2K_DATA_DIR, 'cp2k_force_list_good.txt')
INCOMP_FLIST_PATH = os.path.join(CP2K_DATA_DIR, 'cp2k_force_list_incomp.txt')
# DEF_OUT_PATH = os.path.join(HEADTAIL_DATA_DIR, 'convert_cp2k_forces_input_amend.txt')
# NEW_OUT_PATH = os.path.join(HEADTAIL_DATA_DIR, 'convert_cp2k_forces_input_new.txt')
# PREFIX_OUT_PATH = os.path.join(HEADTAIL_DATA_DIR, 'convert_cp2k_forces_prefixed.txt')
# SUFFIX_OUT_PATH = os.path.join(HEADTAIL_DATA_DIR, 'convert_cp2k_forces_suffix.txt')
# BOTH_OUT_PATH = os.path.join(HEADTAIL_DATA_DIR, 'convert_cp2k_forces_prefix_suffix.txt')

class TestConvertCP2K(unittest.TestCase):
    # def testNoArgs(self):
    #     with capture_stdout(convert_cp2k_forces.main,[]) as output:
    #         self.assertTrue("show this help message" in output)
    #     with capture_stderr(convert_cp2k_forces.main,[]) as output:
    #         self.assertTrue("WARNING:  Default file" in output)
    # def testMissingFileList(self):
    #     with capture_stdout(convert_cp2k_forces.main,["-l", " "]) as output:
    #         self.assertTrue("show this help message" in output)
    #     with capture_stderr(convert_cp2k_forces.main,[]) as output:
    #         self.assertTrue("WARNING:  Default file" in output)
    def testMissingIncompleteFile(self):
        with capture_stderr(convert_cp2k_forces.main,["-l", INCOMP_FLIST_PATH]) as output:
            self.assertTrue("SUM OF ATOMIC FORCES" in output)
            self.assertTrue("Could not read file" in output)
        with capture_stout(convert_cp2k_forces.main,["-l", INCOMP_FLIST_PATH]) as output:
            self.assertTrue("0.957 -0.413  1.283  1.653" in output)

    def testGoodInput(self):
        convert_cp2k_forces.main,["-l", FLIST_PATH]
    # def testAddHead(self):
    #     try:
    #         convert_cp2k_forces.main([INPUT_PATH, "-b", "../"])
    #         self.assertFalse(diff_lines(DEF_OUT_PATH, PREFIX_OUT_PATH))
    #     finally:
    #         silent_remove(DEF_OUT_PATH)
    # def testAddTail(self):
    #     try:
    #         convert_cp2k_forces.main([INPUT_PATH, "-e", ".txt"])
    #         self.assertFalse(diff_lines(DEF_OUT_PATH, SUFFIX_OUT_PATH))
    #     finally:
    #         silent_remove(DEF_OUT_PATH)
    # def testAddBoth(self):
    #     try:
    #         convert_cp2k_forces.main([INPUT_PATH, "-b", "../", "-e", ".txt"])
    #         self.assertFalse(diff_lines(DEF_OUT_PATH, BOTH_OUT_PATH))
    #     finally:
    #         silent_remove(DEF_OUT_PATH)
    # def testSpecifyOutfile(self):
    #     try:
    #         convert_cp2k_forces.main([INPUT_PATH, "-b", "../", "-e", ".txt", "-n", NEW_OUT_PATH ])
    #         self.assertFalse(diff_lines(NEW_OUT_PATH, BOTH_OUT_PATH))
    #     finally:
    #         silent_remove(NEW_OUT_PATH)
    # def testAddNothing(self):
    #     try:
    #         with capture_stderr(convert_cp2k_forces.main,[INPUT_PATH]) as output:
    #             self.assertTrue("Return file will be the same as the input" in output)
    #         self.assertFalse(diff_lines(INPUT_PATH, DEF_OUT_PATH))
    #     finally:
    #         silent_remove(DEF_OUT_PATH)
