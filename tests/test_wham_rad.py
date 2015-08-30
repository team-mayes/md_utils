import logging
import os
import unittest
from md_utils.wham_rad import create_out_fname, OUT_PFX, calc_corr, BOLTZ_CONST, calc_rad, COORD_KEY, CORR_KEY, FREE_KEY, \
    set_zero_point, write_result

# Experimental temperature was 310 Kelvin
INF = "inf"
EXP_TEMP = 310
EXP_KBT = BOLTZ_CONST * EXP_TEMP

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_wham_rad')

DATA_DIR = 'test_data'

ORIG_WHAM_FNAME = "PMFlast2ns3_1.txt"
ORIG_WHAM_PATH = os.path.join(DATA_DIR, ORIG_WHAM_FNAME)

SHORT_WHAM_FNAME = "PMFtest.txt"
SHORT_WHAM_PATH = os.path.join(DATA_DIR, ORIG_WHAM_FNAME)


# Tests #
class TestCreateOutFname(unittest.TestCase):
    def testOutFname(self):
        """
        Check for prefix addition.
        """
        self.assertTrue(create_out_fname(ORIG_WHAM_PATH).endswith(
            os.sep + OUT_PFX + ORIG_WHAM_FNAME))

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
        logger.debug(set_zero_point(calc_rad(SHORT_WHAM_PATH, EXP_KBT)))

class TestWriteOut(unittest.TestCase):

    def testWrite(self):
        write_result(calc_rad(SHORT_WHAM_PATH, EXP_KBT), create_out_fname(SHORT_WHAM_PATH))

