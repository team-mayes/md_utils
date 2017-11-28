# coding=utf-8

"""
Tests for wham_rad.
"""

import unittest
import os
from md_utils.md_common import silent_remove, diff_lines
from md_utils.press_dups import avg_rows, compress_dups, main

__author__ = 'mayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
DUPS_DIR = os.path.join(DATA_DIR, 'press_dups')
HEAD_RAW = os.path.join(DUPS_DIR, 'proc_data_all_head0.75.csv')
HEAD_STD = os.path.join(DUPS_DIR, 'std_proc_data_all_head0.75.csv')
HEAD_PRESS = os.path.join(DUPS_DIR, 'pressed_' + 'proc_data_all_head0.75.csv')


# Shared Methods #

class TestAvgRows(unittest.TestCase):
    def testThree(self):
        data = [{"a": 1.3, "b": 3.0, "c": 8.5}, {"a": 1.3, "b": 1.0, "c": -4.2},
                {"a": 1.3, "b": 2.2, "c": 19.0}]
        avg = avg_rows(data)
        self.assertAlmostEqual(avg['a'], 1.3)
        self.assertAlmostEqual(avg['b'], 2.066666666666)
        self.assertAlmostEqual(avg['c'], 7.766666666666)


class TestPressDups(unittest.TestCase):
    def testThree(self):
        data = [{"a": 1.3, "b": 3.0, "c": 8.5}, {"a": 1.3, "b": 1.0, "c": -4.2},
                {"a": 1.3, "b": 2.2, "c": 19.0}, {"a": 99, "b": 1.0, "c": -4.2},
                {"a": -22, "b": 1.0, "c": -4.2}]
        avg = compress_dups(data, "a")
        self.assertEqual(3, len(avg))


class TestMainNoOutput(unittest.TestCase):
    def testNoArg(self):
        main([])


class TestMain(unittest.TestCase):
    def testWithHead075Data(self):
        try:
            main(argv=[HEAD_RAW])
            self.assertFalse(diff_lines(HEAD_STD, HEAD_PRESS))
        finally:
            silent_remove(HEAD_PRESS)
            # pass
