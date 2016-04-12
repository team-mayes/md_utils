# coding=utf-8

"""
Tests for max_dimen.py.
"""

import unittest
import os

from md_utils import max_dimen
from md_utils.max_dimen import DEF_DIMEN_FILE
from md_utils.md_common import capture_stdout, capture_stderr


__author__ = 'hmayes'

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'small_tests')

# Input files #

DEF_INP = os.path.join(SUB_DATA_DIR, DEF_DIMEN_FILE)
BAD_INPUT = os.path.join(SUB_DATA_DIR, 'bad_max_dimen_input.txt')
BAD_INPUT2 = os.path.join(SUB_DATA_DIR, 'bad_max_dimen_input2.txt')


class TestMaxDimen(unittest.TestCase):
    def testNoArgs(self):
        with capture_stderr(max_dimen.main, []) as output:
            self.assertTrue("Problems reading file" in output)

    def testDefInp(self):
        max_dimen.main(["-f", DEF_INP])
        with capture_stdout(max_dimen.main, ["-f", DEF_INP]) as output:
            self.assertTrue('Maximum value in each dimension:    11.891000    15.605000    18.314000\n'
                            '                With 6 A buffer:    17.891000    21.605000    24.314000' in output)

    def testBadInput(self):
        # Test what happens when cannot convert a value to float
        with capture_stderr(max_dimen.main, ["-f", BAD_INPUT]) as output:
            self.assertTrue("Could not convert the following line to floats" in output)

    def testIncDimen(self):
        # Test what happens when the lines do not all have the same number of dimensions
        with capture_stderr(max_dimen.main, ["-f", BAD_INPUT2]) as output:
            self.assertTrue("Problems reading data" in output)
            self.assertTrue("found 3 values " in output)
            self.assertTrue("and 2 values" in output)
