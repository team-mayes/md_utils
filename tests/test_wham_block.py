# coding=utf-8
"""
Tests for wham_block.
"""
import inspect

import logging
import unittest
import tempfile
import shutil
import os
import md_utils
from md_utils.wham import DEF_BASE_SUBMIT_TPL
from md_utils.wham import DEF_LINE_SUBMIT_TPL

from md_utils.wham_block import (pair_avg,
                                 rmsd_avg, block_average)
from tests.test_wham import (META_PATH, EVEN_DATA, ODD_DATA,
                             ODD_KEY, EVEN_KEY)

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_wham_block')

EVEN_PAIR_AVG = [1.2311619999999999, 1.220716, 1.2131370000000001,
                 1.1924375, 1.262987]

ODD_PAIR_AVG = [1.2474835, 1.2110025, 1.2557155, 1.1911665, 1.228554,
                1.2435805, 1.25972]

TEST_RMSD = {EVEN_KEY: EVEN_DATA, ODD_KEY: ODD_DATA}


# The directory of the md_utils base package
MD_UTILS_BASE = os.path.dirname(inspect.getfile(md_utils))
SKEL_LOC = os.path.join(MD_UTILS_BASE, "skel")
TPL_LOC = os.path.join(SKEL_LOC, "tpl")
SUB_WHAM_BASE_TPL = os.path.join(TPL_LOC, DEF_BASE_SUBMIT_TPL)
SUB_WHAM_LINE_TPL = os.path.join(TPL_LOC, DEF_LINE_SUBMIT_TPL)

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


# TODO: Finish block_average test
class BlockAverage(unittest.TestCase):

    def testBlockAverage(self):
        directory_name = None
        try:
            directory_name = tempfile.mkdtemp()
            block_average(META_PATH, 12, tpl_dir=TPL_LOC, base_dir=directory_name)
        finally:
            shutil.rmtree(directory_name)
