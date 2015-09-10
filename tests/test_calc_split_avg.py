# coding=utf-8

"""
Tests for calc_split_avg.
"""

import logging
import unittest
import os
from md_utils.calc_split_avg import bin_by_pattern, calc_avg_stdev, OUT_FNAME_FMT, write_avg_stdev

__author__ = 'cmayes'

FILES = ['rad_PMF.02_01', 'rad_PMF.02_02', 'rad_PMF.01_02', 'rad_PMF.02_03', 'rad_PMF.01_01']

BINNED_FILES = {'02': ['rad_PMF.02_01', 'rad_PMF.02_02', 'rad_PMF.02_03'], '01': ['rad_PMF.01_02', 'rad_PMF.01_01']}

DATA_DIR = os.path.join('test_data', 'post_rad_wham')

INFILES = [os.path.join(DATA_DIR, radf) for radf in ['rad_PMF.02_01', 'rad_PMF.02_02', 'rad_PMF.02_03']]

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_calc_split_avg')


class TestBinFileNames(unittest.TestCase):
    def testMulti(self):
        self.assertDictEqual(BINNED_FILES, bin_by_pattern(FILES))

class TestDataProcess(unittest.TestCase):
    def testAvgStdev(self):
        results = calc_avg_stdev(INFILES)
        for res_row in results:
            self.assertEqual(3, len(res_row))
            for field in res_row:
                self.assertIsInstance(field, float)


class TestWriteAvg(unittest.TestCase):
    def testAvgStdev(self):
        results = calc_avg_stdev(INFILES)
        write_avg_stdev(results, os.path.join(DATA_DIR, OUT_FNAME_FMT.format("02")))
