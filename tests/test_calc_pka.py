# coding=utf-8

"""
Tests for wham_rad.
"""

import logging
import unittest

import os

from md_utils.calc_pka import calc_pka, NO_MAX_ERR
from md_utils.common import BOLTZ_CONST, read_csv, calc_kbt
from md_utils.wham_rad import (COORD_KEY, CORR_KEY,
                               FREE_KEY)


# Experimental temperature was 310 Kelvin
EXP_TEMP = 310
EXP_KBT = BOLTZ_CONST * EXP_TEMP

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_calc_pka')

DATA_DIR = 'test_data'
PKA_DATA_DIR = os.path.join(DATA_DIR, 'calc_pka')
GOOD_RAD_PATH = os.path.join(PKA_DATA_DIR, 'rad_PMFlast2ns3_1.txt')
NO_MAX_RAD_PATH = os.path.join(PKA_DATA_DIR, 'rad_no_max.txt')

# Shared Methods #


class TestCalcPka(unittest.TestCase):
    def testGood(self):
        pka_val = calc_pka(read_csv(GOOD_RAD_PATH, {FREE_KEY: float,
                                                    CORR_KEY: float,
                                                    COORD_KEY: float, }), calc_kbt(EXP_TEMP))
        logger.debug("PKA: %f", pka_val)

    def testNoMax(self):
        pka_val = calc_pka(read_csv(NO_MAX_RAD_PATH, {FREE_KEY: float,
                                                      CORR_KEY: float,
                                                      COORD_KEY: float, }), calc_kbt(EXP_TEMP))
        self.assertEqual(NO_MAX_ERR, pka_val)
