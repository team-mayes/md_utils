# coding=utf-8

"""
Tests for wham.
"""

import shutil
import tempfile
import unittest

import os
import re
from md_utils.wham import (read_meta, read_meta_rmsd, write_rmsd, read_rmsd,
                           LINES_KEY, DIR_KEY, LOC_KEY)
from md_utils.wham_block import write_meta

# Constants #

DATA_DIR = os.path.join('test_data', 'wham_test_data')
META_00_FNAME = 'meta.00'
META_PATH = os.path.join(DATA_DIR, META_00_FNAME)
EVEN_DATA = [1.201687, 1.260637, 1.242285, 1.199147, 1.175087, 1.251187,
             1.210499, 1.174376, 1.245316, 1.280658, ]
ODD_DATA = [1.248430, 1.246537, 1.243088, 1.178917, 1.268993, 1.242438,
            1.204454, 1.177879, 1.173452, 1.283656, 1.217349, 1.269812,
            1.286239, 1.233201, 1.272090]
ODD_KEY = "odd"
EVEN_KEY = "even"

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


class WriteRmsd(unittest.TestCase):
    def testWriteRmsd(self):
        directory_name = None
        try:
            directory_name = tempfile.mkdtemp()
            rfname = os.path.join(directory_name, EVEN_KEY)
            write_rmsd(EVEN_DATA, rfname)
            self.assertAlmostEqual(EVEN_DATA, read_rmsd(rfname))
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
