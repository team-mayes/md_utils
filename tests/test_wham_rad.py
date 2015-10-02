# coding=utf-8

"""
Tests for wham_rad.
"""

import logging
import unittest
import math

import os

from md_utils.common import BOLTZ_CONST
from md_utils.wham_rad import calc_corr, calc_rad, to_zero_point
from md_utils.wham import CORR_KEY, COORD_KEY, FREE_KEY


# Experimental temperature was 310 Kelvin
INF = "inf"
EXP_TEMP = 310
EXP_KBT = BOLTZ_CONST * EXP_TEMP

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_wham_rad')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

ORIG_WHAM_FNAME = "PMFlast2ns3_1.txt"
ORIG_WHAM_PATH = os.path.join(DATA_DIR, ORIG_WHAM_FNAME)

SHORT_WHAM_FNAME = "PMFtest.txt"
SHORT_WHAM_PATH = os.path.join(DATA_DIR, ORIG_WHAM_FNAME)

# Shared Methods #


def zpe_check(test_inst, zpe):
    """Tests that the zero-point energy value has been properly applied.
    :param test_inst: The test class instance.
    :param zpe: The zpe-calibrated data to test.
    """
    for zrow in zpe:
        corr, coord = float(zrow[CORR_KEY]), float(zrow[COORD_KEY])
        if corr == 0:
            test_inst.assertAlmostEqual(6.0, coord)
        else:
            test_inst.assertTrue(corr < 0.0 or math.isinf(corr))

# Tests #


class TestCalcCorr(unittest.TestCase):
    def testCalcCorr(self):
        """
        Good sample data.
        """
        self.assertAlmostEqual(11.9757045375, calc_corr(2.050000, 9.532083, EXP_KBT))

    def testCalcCorrNaN(self):
        """
        Unparsed free energy value.
        """
        self.assertEqual(INF, calc_corr(2.050000, INF, EXP_KBT))


class TestCalcRad(unittest.TestCase):
    def testCalcRad(self):
        for row in calc_rad(SHORT_WHAM_PATH, EXP_KBT):
            self.assertEqual(3, len(row))
            self.assertIsInstance(row[COORD_KEY], float)
            self.assertIsInstance(row[CORR_KEY], float)
            self.assertIsInstance(row[FREE_KEY], float)


class TestZeroPoint(unittest.TestCase):

    def testZeroPoint(self):
        zpe = to_zero_point(calc_rad(SHORT_WHAM_PATH, EXP_KBT))
        zpe_check(self, zpe)
