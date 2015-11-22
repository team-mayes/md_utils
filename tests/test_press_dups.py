# coding=utf-8

"""
Tests for wham_rad.
"""

import logging

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_press_dups')

import unittest
import os
from md_utils import press_dups
from md_utils.md_common import silent_remove, diff_lines
from md_utils.press_dups import avg_rows, compress_dups

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
DUPS_DIR = os.path.join(DATA_DIR, 'press_dups')
WHIT_RAW = os.path.join(DUPS_DIR, 'proc_data_all_withhead0.75.csv')
WHIT_STD = os.path.join(DUPS_DIR, 'std_proc_data_all_withhead0.75.csv')
WHIT_PRESS = os.path.join(DUPS_DIR, 'pressed_' + 'proc_data_all_withhead0.75.csv')


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
        self.assertEquals(3, len(avg))


class TestFromMain(unittest.TestCase):
    def testWhithead075Data(self):
        try:
            press_dups.main(argv=[WHIT_RAW])
            self.assertEqual(0, len(diff_lines(WHIT_STD, WHIT_PRESS)))
        finally:
            silent_remove(WHIT_PRESS)
