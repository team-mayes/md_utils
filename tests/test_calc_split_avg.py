# coding=utf-8

"""
Tests for calc_split_avg.
"""

import shutil
import tempfile
import unittest

import os

from md_utils.calc_split_avg import bin_by_pattern, calc_avg_stdev, OUT_FNAME_FMT, write_avg_stdev, OUT_KEY_SEQ, \
    AVG_KEY_CONV, main
from md_utils.md_common import read_csv, diff_lines, silent_remove, capture_stderr, capture_stdout

__author__ = 'mayes'

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data', 'post_rad_wham')


# Test input files #

IN_FILES = [os.path.join(DATA_DIR, rad_f) for rad_f in ['rad_PMF.02_01', 'rad_PMF.02_02', 'rad_PMF.02_03']]


# Test data #

FILES = ['rad_PMF.02_01', 'rad_PMF.02_02', 'rad_PMF.01_02', 'rad_PMF.02_03', 'rad_PMF.01_01']
BINNED_FILES = {'02': ['rad_PMF.02_01', 'rad_PMF.02_02', 'rad_PMF.02_03'], '01': ['rad_PMF.01_02', 'rad_PMF.01_01']}


# Output files #

# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(DATA_DIR, 'avg_rad_PMF.02.csv')
GOOD_OUT = os.path.join(DATA_DIR, 'avg_rad_PMF.02_Good.csv')


class TestBinFileNames(unittest.TestCase):
    def testMulti(self):
        self.assertDictEqual(BINNED_FILES, bin_by_pattern(FILES))


class TestDataProcess(unittest.TestCase):
    def testAvgStDev(self):
        results = calc_avg_stdev(IN_FILES)
        for res_row in results:
            self.assertEqual(3, len(res_row))
            for field in res_row:
                self.assertIsInstance(field, float)


class TestWriteAvg(unittest.TestCase):
    def testAvgStdev(self):
        results = calc_avg_stdev(IN_FILES)
        directory_name = None
        try:
            directory_name = tempfile.mkdtemp()
            tgt_file = OUT_FNAME_FMT.format("02")
            write_avg_stdev(results, tgt_file, basedir=directory_name)
            csv_data = read_csv(os.path.join(directory_name, tgt_file), data_conv=AVG_KEY_CONV)
            for entry in csv_data:
                self.assertEqual(3, len(entry))
                for c_key, c_val in entry.items():
                    self.assertIsInstance(c_val, float)
                    self.assertTrue(c_key in OUT_KEY_SEQ)
        finally:
            shutil.rmtree(directory_name)


class TestMain(unittest.TestCase):
    def testDefault(self):
        try:
            main(["-o"])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT)

    def testNoSuchOption(self):
        # main(["-@", DEF_OUT])
        with capture_stderr(main, ["-@", DEF_OUT]) as output:
            self.assertTrue("unrecognized argument" in output)
            self.assertTrue(DEF_OUT in output)
        with capture_stdout(main, ["-@", DEF_OUT]) as output:
            self.assertTrue("optional arguments" in output)
