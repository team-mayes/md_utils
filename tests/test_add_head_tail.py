# coding=utf-8

"""
Tests for add_head_tail.py.
"""

import logging
import unittest

import os
from md_utils import add_head_tail
import sys
from cStringIO import StringIO
from contextlib import contextmanager
from md_utils.md_common import capture_stdout, capture_stderr


__author__ = 'hmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
ADD_DATA_DIR = os.path.join(DATA_DIR, 'small_tests')
GOOD_ADD_PATH = os.path.join(ADD_DATA_DIR, 'rad_PMFlast2ns3_1.txt')

# Shared Methods #



class TestAddHeadTail(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(add_head_tail.main,[]) as output:
            self.assertTrue("usage:" in output)
        with capture_stderr(add_head_tail.main,[]) as output:
            self.assertTrue("too few arguments" in output)
    def testAddHead(self):
        pass
    def testAddTail(self):
        pass
    def testAddBoth(self):
        with capture_stderr(add_head_tail.main,["job_list.txt"]) as output:
            self.assertTrue("Return file will be the same as the input" in output)

    def testAddNothing(self):
        pass


