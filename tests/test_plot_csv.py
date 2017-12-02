# coding=utf-8

"""
"""

import unittest
import os
from md_utils.md_common import silent_remove, diff_lines
from md_utils.plot_csv import main

__author__ = 'mayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
CSV_DIR = os.path.join(DATA_DIR, 'plot_csv')
CSV_FILE = os.path.join(CSV_DIR, 'identity.csv')
PNG_FILE = os.path.join(CSV_DIR, 'identity.png')


class TestMainNoOutput(unittest.TestCase):
    def testNoArg(self):
        main([])


class TestMain(unittest.TestCase):
    def testWithHead075Data(self):
        try:
            main(argv=[CSV_FILE])
            # self.assertFalse(diff_lines(HEAD_STD, HEAD_PRESS))
        finally:
            silent_remove(PNG_FILE)
