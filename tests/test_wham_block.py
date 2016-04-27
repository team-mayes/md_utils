# coding=utf-8
"""
Tests for wham_block.
"""
import filecmp
import inspect

import logging
import unittest
import tempfile
import shutil
import os
import md_utils
from md_utils.wham import DEF_BASE_SUBMIT_TPL
from md_utils.wham import DEF_LINE_SUBMIT_TPL
from md_utils.wham_block import (pair_avg, rmsd_avg, block_average, main)
from tests.test_wham import (META_PATH, EVEN_DATA, ODD_DATA,
                             ODD_KEY, EVEN_KEY)

__author__ = 'cmayes'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'wham_test_data')
GOOD_OUT_DIR = os.path.join(SUB_DATA_DIR, 'good_block_out')

# The directory of the md_utils base package
MD_UTILS_BASE = os.path.dirname(inspect.getfile(md_utils))
SKEL_LOC = os.path.join(MD_UTILS_BASE, "skel")
TPL_LOC = os.path.join(SKEL_LOC, "tpl")
SUB_WHAM_BASE_TPL = os.path.join(TPL_LOC, DEF_BASE_SUBMIT_TPL)
SUB_WHAM_LINE_TPL = os.path.join(TPL_LOC, DEF_LINE_SUBMIT_TPL)

EVEN_PAIR_AVG = [1.2311619999999999, 1.220716, 1.2131370000000001,
                 1.1924375, 1.262987]

ODD_PAIR_AVG = [1.2474835, 1.2110025, 1.2557155, 1.1911665, 1.228554,
                1.2435805, 1.25972]

TEST_RMSD = {EVEN_KEY: EVEN_DATA, ODD_KEY: ODD_DATA}


# Tests #

class TestAveraging(unittest.TestCase):
    def testEvenPairs(self):
        avg = pair_avg(EVEN_DATA)
        self.assertAlmostEqual(EVEN_PAIR_AVG, avg)

    def testOddPairs(self):
        avg = pair_avg(ODD_DATA)
        self.assertAlmostEqual(ODD_PAIR_AVG, avg)


class RmsdAverage(unittest.TestCase):
    def testRmsdAveragePair(self):
        avg = rmsd_avg(TEST_RMSD, pair_avg)
        self.assertAlmostEqual(EVEN_PAIR_AVG, avg[EVEN_KEY])
        self.assertAlmostEqual(ODD_PAIR_AVG, avg[ODD_KEY])


class BlockAverage(unittest.TestCase):
    def testBlockAverage(self):
        directory_name = None
        try:
            directory_name = tempfile.mkdtemp()
            block_average(META_PATH, 12, tpl_dir=TPL_LOC, base_dir=directory_name)
            dir_cmp = (filecmp.dircmp(directory_name, GOOD_OUT_DIR))
            self.assertFalse(dir_cmp.diff_files)
        finally:
            shutil.rmtree(directory_name)

class TestMain(unittest.TestCase):
    def testDefaults(self):
        main([])