# coding=utf-8

"""
Tests for call_vmd.py.
"""
import os
import unittest
import logging
from md_utils.call_vmd import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
VMD_DIR = os.path.join(DATA_DIR, 'call_vmd')

PSF = os.path.join(VMD_DIR, "open_xylose.psf")
PDB = os.path.join(VMD_DIR, "open_xylose.pdb")
TCL_SCRIPT = os.path.join(VMD_DIR, "prot.tcl")


class TestFailWell(unittest.TestCase):
    def testNoArgs(self):
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("arguments:" in output)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("required" in output)

    def testMissingFile(self):
        test_input = ["ghost.txt", "-e", ".txt"]
        with capture_stderr(main, test_input) as output:
            self.assertTrue("No such file or directory" in output)


class TestMain(unittest.TestCase):
    # These will show example usage
    def testAddNothing(self):
        # this first test does not really doing anything, and warns the user
        try:
            with capture_stderr(main, [INPUT_PATH]) as output:
                self.assertTrue("Return file will be the same as the input" in output)
            self.assertFalse(diff_lines(INPUT_PATH, DEF_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH, DISABLE_REMOVE)

    def testAddHead(self):
        try:
            main([INPUT_PATH, "-b", "../"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, PREFIX_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testAddTail(self):
        try:
            main([INPUT_PATH, "-e", ".txt"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, SUFFIX_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testAddBoth(self):
        try:
            main([INPUT_PATH, "-b", "../", "-e", ".txt"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, BOTH_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testSpecifyOutfile(self):
        try:
            main([INPUT_PATH, "-b", "../", "-e", ".txt", "-n", NEW_OUT_PATH])
            self.assertFalse(diff_lines(NEW_OUT_PATH, BOTH_OUT_PATH))
        finally:
            silent_remove(NEW_OUT_PATH)

