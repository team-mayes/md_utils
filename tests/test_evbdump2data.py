# coding=utf-8

"""
Tests for evbdump2data
"""
import os
import unittest

from md_utils import evbdump2data
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'


DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'evbd2d')
INCOMP_INI_PATH = os.path.join(SUB_DATA_DIR, 'evbd2d_missing_data.ini')
GOOD_INI_PATH = os.path.join(SUB_DATA_DIR, 'evbd2d_good.ini')
GOOD_INI_NO_CHARGE_PATH = os.path.join(SUB_DATA_DIR, 'evbd2d_good_no_section_atom_nums.ini')
DEF_PROT_OUT_PATH = os.path.join(SUB_DATA_DIR, 'serca_prot_deprot_10.data')
DEF_DEPROT_OUT_PATH = os.path.join(SUB_DATA_DIR, 'serca_prot_deprot_20.data')
GOOD_PROT_OUT_PATH = os.path.join(SUB_DATA_DIR, 'serca_prot_good.data')
GOOD_DEPROT_OUT_PATH = os.path.join(SUB_DATA_DIR, 'serca_deprot_good.data')
REPROD_TPL = os.path.join(DATA_DIR, 'reproduced_tpl.data')
REPROD2_TPL = os.path.join(os.path.dirname(__file__), 'reproduced_tpl.data')

class TestEVBDump2Data(unittest.TestCase):
    def testNoIni(self):
        with capture_stdout(evbdump2data.main,[]) as output:
            self.assertTrue("usage:" in output)
        with capture_stderr(evbdump2data.main,[]) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)
    def testMissingConfig(self):
        with capture_stderr(evbdump2data.main,["-c", INCOMP_INI_PATH]) as output:
            self.assertTrue("Input data missing" in output)
        with capture_stdout(evbdump2data.main,["-c", INCOMP_INI_PATH]) as output:
            self.assertTrue("optional arguments" in output)
    def testMakeData(self):
        with capture_stdout(evbdump2data.main,["-c", GOOD_INI_PATH]) as output:
            # Checking intermediate charge calculation
            self.assertTrue("After atom 15436 (last_p1), the total charge is: -26.000" in output)
        with capture_stderr(evbdump2data.main,["-c", GOOD_INI_PATH]) as output:
            # Make sure it handles the extra empty line
            self.assertFalse("WARNING:  Problems reading file" in output)
        try:
            self.assertFalse(diff_lines(DEF_PROT_OUT_PATH, GOOD_PROT_OUT_PATH))
            self.assertFalse(diff_lines(DEF_DEPROT_OUT_PATH, GOOD_DEPROT_OUT_PATH))
        finally:
            silent_remove(DEF_PROT_OUT_PATH)
            silent_remove(DEF_DEPROT_OUT_PATH)
            silent_remove(REPROD2_TPL)
    def testNoChargeCheck(self):
        with capture_stdout(evbdump2data.main,["-c", GOOD_INI_NO_CHARGE_PATH]) as output:
            # Checking intermediate charge calculation
            self.assertTrue("FYI: the total system charge is < 1e-06" in output)
    def testIncompDump(self):
        with capture_stderr(evbdump2data.main,["-c", GOOD_INI_NO_CHARGE_PATH]) as output:
            # Make sure it handles the extra empty line
            self.assertTrue("did not have the full list of atom numbers" in output)
        try:
            self.assertFalse(diff_lines(DEF_PROT_OUT_PATH, GOOD_PROT_OUT_PATH))
            self.assertFalse(diff_lines(DEF_DEPROT_OUT_PATH, GOOD_DEPROT_OUT_PATH))
        finally:
            silent_remove(DEF_PROT_OUT_PATH)
            silent_remove(DEF_DEPROT_OUT_PATH)
            silent_remove(REPROD_TPL)




