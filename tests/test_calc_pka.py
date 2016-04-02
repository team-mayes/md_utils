# coding=utf-8

"""
Tests for wham_rad.
"""

import unittest
import os

from md_utils.calc_pka import calc_pka, NO_MAX_ERR, NoMaxError
from md_utils.md_common import read_csv, calc_kbt
from md_utils.wham import CORR_KEY, COORD_KEY, FREE_KEY


__author__ = 'cmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
PKA_DATA_DIR = os.path.join(DATA_DIR, 'calc_pka')
GOOD_RAD_PATH = os.path.join(PKA_DATA_DIR, 'rad_PMF_last2ns3_1.txt')
NO_MAX_RAD_PATH = os.path.join(PKA_DATA_DIR, 'rad_PMF_no_max.txt')

# Experimental temperature was 310 Kelvin
EXP_TEMP = 310


class TestCalcPka(unittest.TestCase):
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
