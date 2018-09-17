# coding=utf-8

"""
Tests for call_vmd.py.
"""
import os
import unittest
import logging
from md_utils.call_vmd import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove

__author__ = 'adams'

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
VMD_DIR = os.path.join(DATA_DIR, 'call_vmd')

OUT_DIR = os.path.join('test_data', 'call_vmd')
PSF = os.path.join(VMD_DIR, "open_xylose.psf")
PDB = os.path.join(VMD_DIR, "open_xylose.pdb")
TCL_SCRIPT = os.path.join(VMD_DIR, "prot.tcl")
PROT_OUT = os.path.join(VMD_DIR, "output.pdb")
GOOD_PROT_OUT = os.path.join(VMD_DIR, "prot_good.pdb")
DCD_UNBOUND = os.path.join(VMD_DIR, 'short_unbound.dcd')
DCD_BOUND = os.path.join(VMD_DIR, 'short_bound.dcd')
DCD_TOP = os.path.join(VMD_DIR, 'step5_assembly.xplor_ext.psf')
SUGAR_SCRIPT = os.path.join(VMD_DIR, 'sugar_check.tcl')
UNBOUND_OUT = os.path.join(VMD_DIR, 'output')
BOUND_OUT = os.path.join(VMD_DIR, 'output')
GOOD_UNBOUND_OUT = os.path.join(VMD_DIR, 'unbound_good.txt')
GOOD_BOUND_OUT = os.path.join(VMD_DIR, 'bound_good.txt')


class TestFailWell(unittest.TestCase):
    def testNoArgs(self):
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("arguments:" in output)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Found no" in output)

    def testMissingFile(self):
        test_input = ["-t", "ghost.txt", "-s", "ghost.tcl"]
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not find" in output)


class TestMain(unittest.TestCase):
    # These will show example usage
    def testProtTcl(self):
        # todo: fix test
        test_input = ["-t", PDB, "-p", PSF, "-s", TCL_SCRIPT, "-o", VMD_DIR]
        try:
            main(test_input)
            os.path.isfile(PROT_OUT)
            self.assertFalse(diff_lines(PROT_OUT, GOOD_PROT_OUT))
        finally:
            silent_remove(PROT_OUT, DISABLE_REMOVE)

    def testArgText(self):
        # todo: fix test
        test_input = ["-t", PDB, "-p", PSF, "-s", TCL_SCRIPT, "-o", VMD_DIR, "-a", 'arg']
        try:
            main(test_input)
            self.assertFalse(diff_lines(PROT_OUT, GOOD_PROT_OUT))
        finally:
            silent_remove(PROT_OUT, DISABLE_REMOVE)

    def testArgList(self):
        # todo: fix test
        test_input = ["-t", PDB, "-p", PSF, "-s", TCL_SCRIPT, "-o", VMD_DIR, "-a", ['arg1', 'arg2']]
        try:
            main(test_input)
            self.assertFalse(diff_lines(PROT_OUT, GOOD_PROT_OUT))
        finally:
            silent_remove(PROT_OUT, DISABLE_REMOVE)

    def testCheckSugarBound(self):
        # todo: fix test
        test_input = ["-t", DCD_BOUND, "-p", DCD_TOP, "-s", SUGAR_SCRIPT, "-o", VMD_DIR, "-a", '1']
        try:
            main(test_input)
            self.assertFalse(diff_lines(BOUND_OUT, GOOD_BOUND_OUT))
        finally:
            silent_remove(BOUND_OUT, disable=DISABLE_REMOVE)

