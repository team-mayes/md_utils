# coding=utf-8

"""
Tests for evb_get_info.py.
Also, test diff_lines
"""
import os
import unittest
from md_utils.evb_chk_get_info import main, DEF_CFG_FILE
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
import logging

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'


# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'evb_chk')

# Input files to catch if fails well #
MISSING_KEY_INI = os.path.join(SUB_DATA_DIR, 'evb_chk_get_info_missing_key.ini')
NO_EXCLUDE_INI = os.path.join(SUB_DATA_DIR, 'evb_chk_get_info_no_exclude.ini')
WRONG_CHARGE_INI = os.path.join(SUB_DATA_DIR, 'evb_chk_get_info_wrong_expected_charge.ini')

# Input files paired with output #
DEF_INI = os.path.join(SUB_DATA_DIR, DEF_CFG_FILE)
VMD_OUT = os.path.join(SUB_DATA_DIR, 'vmd_water_0.625_20c_short_reorder_545000.dat')
GOOD_VMD_OUT = os.path.join(SUB_DATA_DIR, 'vmd_water_0.625_20c_short_reorder_545000_good.dat')
WATER_OUT = os.path.join(SUB_DATA_DIR, 'water_0.625_20c_short_reorder_545000.dat')
GOOD_WATER_OUT = os.path.join(SUB_DATA_DIR, 'water_0.625_20c_short_reorder_545000_good.dat')

CHECK_CHARGE_INI = os.path.join(SUB_DATA_DIR, "evb_chk_get_info_expected_charge.ini")

REL_E_INI = os.path.join(SUB_DATA_DIR, "evb_chk_get_ene.ini")
REL_E_OUT = os.path.join(SUB_DATA_DIR, "chk_glu_list_sum.csv")
GOOD_REL_E_OUT = os.path.join(SUB_DATA_DIR, "chk_glu_list_sum_good.csv")


class TestCHKGetInfoFailWell(unittest.TestCase):
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoArgsIni(self):
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments:" in output)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)

    def testMissingInfo(self):
        test_input = ["-c", MISSING_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, ["-c", test_input]) as output:
            self.assertTrue("Missing config val" in output)

    def testNoExclude(self):
        with capture_stderr(main, ["-c", NO_EXCLUDE_INI]) as output:
            self.assertTrue("Expected atom types" in output)

    def testWrongCharge(self):
        with capture_stderr(main, ["-c", WRONG_CHARGE_INI]) as output:
            self.assertTrue("Expected a total charge of +2 but found +1" in output)


class TestCHKGetInfo(unittest.TestCase):
    def testGood(self):
        try:
            test_input = ["-c", DEF_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("total charge" in output)
            self.assertFalse(diff_lines(VMD_OUT, GOOD_VMD_OUT))
            self.assertFalse(diff_lines(WATER_OUT, GOOD_WATER_OUT))
        finally:
            silent_remove(VMD_OUT)
            silent_remove(WATER_OUT)

    def testCheckCharge(self):
        try:
            test_input = ["-c", CHECK_CHARGE_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertFalse("total charge" in output)
        finally:
            silent_remove(VMD_OUT, disable=DISABLE_REMOVE)
            silent_remove(WATER_OUT, disable=DISABLE_REMOVE)

    def testRelativeEnergy(self):
        try:
            test_input = ["-c", REL_E_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("44.822" in output)
            self.assertFalse(diff_lines(REL_E_OUT, GOOD_REL_E_OUT))
        finally:
            silent_remove(REL_E_OUT, disable=DISABLE_REMOVE)
