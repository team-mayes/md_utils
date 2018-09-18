# coding=utf-8

"""
Tests for call_vmd.py.
"""
import os
import unittest
import logging
from md_utils.check_sugar import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove

__author__ = 'xadams'

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
UNBOUND_OUT = os.path.join(VMD_DIR, 'short_unbound.txt')
BOUND_OUT = os.path.join(VMD_DIR, 'short_bound.txt')
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
        test_input = ["-t", "ghost.txt"]
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not find" in output)


class TestMain(unittest.TestCase):
    # These will show example usage
    def testCheckSugarBound(self):
        # todo: fix test
        test_input = ["-t", DCD_BOUND, "-p", DCD_TOP, "-o", VMD_DIR, "-s", SUGAR_SCRIPT, "-k", "-a", '1']
        try:
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("bound in all frames" in output)
            self.assertFalse(diff_lines(BOUND_OUT, GOOD_BOUND_OUT))
        finally:
            silent_remove(BOUND_OUT, disable=DISABLE_REMOVE)

    def testCheckSugarUnbound(self):
        # todo: fix test
        test_input = ["-t", DCD_UNBOUND, "-p", DCD_TOP, "-o", VMD_DIR, "-s", SUGAR_SCRIPT, "-a", '1']
        try:
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("Sugar is unbound" in output)
            self.assertFalse(diff_lines(UNBOUND_OUT, GOOD_UNBOUND_OUT))
        finally:
            silent_remove(UNBOUND_OUT, disable=DISABLE_REMOVE)
