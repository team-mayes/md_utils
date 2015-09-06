# coding=utf-8
"""
Tests for wham_block.
"""


import logging
import os
import unittest
import re
import tempfile
import shutil

from md_utils.wham_block import read_meta, LOC_KEY, DIR_KEY, LINES_KEY, read_meta_rmsd, pair_avg, rmsd_avg, write_rmsd, \
    read_rmsd, write_meta, block_average

ODD_KEY = "odd"

EVEN_KEY = "even"

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_wham_block')

DATA_DIR = os.path.join('test_data', 'wham_test_data')

META_00_FNAME = 'meta.00'
META_PATH = os.path.join(DATA_DIR, META_00_FNAME)

EVEN_DATA = [1.201687, 1.260637, 1.242285, 1.199147, 1.175087, 1.251187,
             1.210499, 1.174376, 1.245316, 1.280658, ]
EVEN_PAIR_AVG = [1.2311619999999999, 1.220716, 1.2131370000000001,
                 1.1924375, 1.262987]

ODD_DATA = [1.248430, 1.246537, 1.243088, 1.178917, 1.268993, 1.242438,
            1.204454, 1.177879, 1.173452, 1.283656, 1.217349, 1.269812,
            1.286239, 1.233201, 1.272090]
ODD_PAIR_AVG = [1.2474835, 1.2110025, 1.2557155, 1.1911665, 1.228554,
                1.2435805, 1.25972]
TEST_RMSD = {EVEN_KEY: EVEN_DATA, ODD_KEY: ODD_DATA}


# Tests #
class TestReadData(unittest.TestCase):
    def testReadMeta(self):
        meta = read_meta(META_PATH)
        self.assertEqual(META_PATH, meta[LOC_KEY])
        self.assertEqual(os.path.abspath(DATA_DIR), meta[DIR_KEY])
        for line in meta[LINES_KEY]:
            self.assertEqual(4, len(line))
            self.assertTrue('RMSD' in line[0])

    def testReadRmsd(self):
        meta = read_meta(META_PATH)
        rmsd_data = read_meta_rmsd(meta)
        pat = re.compile("RMSD.+\.txt")
        for rfile, data in rmsd_data.items():
            self.assertTrue(pat.match(rfile))
            self.assertEqual(2000, len(data))
            for dval in data:
                self.assertIsInstance(dval, float)


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


class WriteRmsd(unittest.TestCase):
    def testWriteRmsd(self):
        directory_name = None
        try:
            directory_name = tempfile.mkdtemp()
            write_rmsd(directory_name, TEST_RMSD)
            self.assertAlmostEqual(EVEN_DATA, read_rmsd(os.path.join(directory_name, EVEN_KEY)))
            self.assertAlmostEqual(ODD_DATA, read_rmsd(os.path.join(directory_name, ODD_KEY)))
        finally:
            shutil.rmtree(directory_name)


class WriteMeta(unittest.TestCase):
    def testWriteMeta(self):
        directory_name = None
        try:
            meta = read_meta(META_PATH)
            directory_name = tempfile.mkdtemp()
            write_meta(directory_name, meta, 8)
            result = read_meta(os.path.join(directory_name, "meta.08"))

            for i, mline in enumerate(result[LINES_KEY]):
                self.assertTrue(mline[0].startswith("08"))
                self.assertEqual(mline[1:], meta[LINES_KEY][i][1:])

        finally:
            shutil.rmtree(directory_name)


class BlockAverage(unittest.TestCase):

    def testBlockAverage(self):
        directory_name = None
        try:
            directory_name = tempfile.mkdtemp()
            block_average(META_PATH, 12, base_dir=directory_name)
        finally:
            shutil.rmtree(directory_name)
