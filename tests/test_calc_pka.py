# coding=utf-8

"""
Tests for wham_rad.
"""

import unittest
import os
import logging
from md_utils.calc_pka import calc_pka, NO_MAX_ERR, NoMaxError, main
from md_utils.md_common import read_csv, calc_kbt, capture_stderr, diff_lines, silent_remove
from md_utils.wham import CORR_KEY, COORD_KEY, FREE_KEY

__author__ = 'mayes'

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
PKA_DATA_DIR = os.path.join(DATA_DIR, 'calc_pka')
GOOD_RAD_PATH = os.path.join(PKA_DATA_DIR, 'rad_PMF_last2ns3_1.txt')
NO_MAX_RAD_PATH = os.path.join(PKA_DATA_DIR, 'rad_PMF_no_max.txt')
DATA_EDIT_DIR = os.path.join(DATA_DIR, 'data_edit')

WRONG_IN_FILE = os.path.join(PKA_DATA_DIR, 'pKa.rad_PMF_defineTS_good.txt')

# noinspection PyUnresolvedReferences
DEF_FILE_OUT = os.path.join(PKA_DATA_DIR, 'pKa.rad_PMF_last2ns3_1.txt')
GOOD_FILE_OUT = os.path.join(PKA_DATA_DIR, 'pKa.rad_PMF_last2ns3_1_good.txt')
GOOD_TS_OUT = os.path.join(PKA_DATA_DIR, 'pKa.rad_PMF_defineTS_good.txt')
# noinspection PyUnresolvedReferences
DEF_DIR_OUT = os.path.join(DATA_DIR, 'pKa.calc_pka')
GOOD_DIR_OUT = os.path.join(PKA_DATA_DIR, 'pKa.calc_pka_good')

# Experimental temperature was 310 Kelvin
EXP_TEMP = 310


class TestCalcPkaPortions(unittest.TestCase):
    def testGood(self):
        pka_val = calc_pka(read_csv(GOOD_RAD_PATH,
                                    data_conv={FREE_KEY: float, CORR_KEY: float, COORD_KEY: float, }),
                           calc_kbt(EXP_TEMP))
        self.assertAlmostEqual(4.7036736, pka_val[0])

    def testNoMax(self):
        with self.assertRaises(NoMaxError) as context:
            calc_pka(read_csv(NO_MAX_RAD_PATH,
                              data_conv={FREE_KEY: float, CORR_KEY: float, COORD_KEY: float, }),
                     calc_kbt(EXP_TEMP))
        self.assertTrue(NO_MAX_ERR in context.exception.args)


class TestCalcPkaNoOutput(unittest.TestCase):
    # Test how program handles imperfect/incomplete options/data
    def testTooFewArg(self):
        test_input = ["-d", PKA_DATA_DIR]
        # main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("following arguments are required" in output)

    def testNoFile(self):
        with capture_stderr(main, [str(EXP_TEMP), "-f", "ghost.csv"]) as output:
            self.assertTrue("No such file or directory: 'ghost.csv'" in output)

    def testNoDir(self):
        with capture_stderr(main, [str(EXP_TEMP), "-d", "ghost"]) as output:
            self.assertTrue("WARNING:  No files found in specified directory 'ghost'" in output)


class TestCalcPkaMain(unittest.TestCase):
    def testGoodDir(self):
        try:
            main([str(EXP_TEMP), "-d", PKA_DATA_DIR, "-o"])
            self.assertFalse(diff_lines(DEF_DIR_OUT, GOOD_DIR_OUT))
        finally:
            silent_remove(DEF_DIR_OUT, disable=DISABLE_REMOVE)

    def testGoodFile(self):
        try:
            main([str(EXP_TEMP), "-f", GOOD_RAD_PATH, "-o"])
            self.assertFalse(diff_lines(DEF_FILE_OUT, GOOD_FILE_OUT))
        finally:
            silent_remove(DEF_FILE_OUT, disable=DISABLE_REMOVE)

    def testDefineTS(self):
        """
        In addition to testing the case where a TS location is defined, tests for overwriting file warning
        """
        try:
            test_input = [str(EXP_TEMP), "-f", GOOD_RAD_PATH, "-o", "-c", "2.4"]
            main(test_input)
            self.assertFalse(diff_lines(DEF_FILE_OUT, GOOD_TS_OUT))
        finally:
            silent_remove(DEF_FILE_OUT, disable=DISABLE_REMOVE)
