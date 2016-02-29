# coding=utf-8

"""
Tests for max_dimen.py.
"""

import unittest
import os

from md_utils import max_dimen
from md_utils.md_common import capture_stdout


__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'small_tests')
INPUT2 = os.path.join(SUB_DATA_DIR, 'max_dimen_input.txt')


class TestMaxDimen(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(max_dimen.main,[]) as output:
            self.assertTrue("Maximum value in each dimension: [ 11.89100027  15.60500002  18.31400013]\nWith 6 A buffer: [ 17.89100027  21.60500002  24.31400013]\n" in output)
    def testSpecifyFile(self):
        with capture_stdout(max_dimen.main,["-f", INPUT2]) as output:
            self.assertTrue("Maximum value in each dimension: [ 13.15199995  15.38499975  18.19799995]\nWith 6 A buffer: [ 19.15199995  21.38499975  24.19799995]\n" in output)
