# coding=utf-8

"""
Tests for calc_split_avg.
"""

import logging
import shutil
import tempfile
import unittest

import os

from md_utils.calc_split_avg import bin_by_pattern, calc_avg_stdev, OUT_FNAME_FMT, write_avg_stdev, OUT_KEY_SEQ, \
    AVG_KEY_CONV
from md_utils.common import read_csv

__author__ = 'cmayes'

FILES = ['rad_PMF.02_01', 'rad_PMF.02_02', 'rad_PMF.01_02', 'rad_PMF.02_03', 'rad_PMF.01_01']

BINNED_FILES = {'02': ['rad_PMF.02_01', 'rad_PMF.02_02', 'rad_PMF.02_03'], '01': ['rad_PMF.01_02', 'rad_PMF.01_01']}

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data', 'post_rad_wham')

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
        directory_name = None
        try:
            directory_name = tempfile.mkdtemp()
            tgt_file = OUT_FNAME_FMT.format("02")
            write_avg_stdev(results, tgt_file, basedir=directory_name)
            csv_data = read_csv(os.path.join(directory_name, tgt_file), data_conv=AVG_KEY_CONV)
            logger.debug(csv_data)
            for entry in csv_data:
                self.assertEqual(3, len(entry))
                for ckey, cval in entry.items():
                    self.assertIsInstance(cval, float)
                    self.assertTrue(ckey in OUT_KEY_SEQ)
        finally:
            shutil.rmtree(directory_name)
