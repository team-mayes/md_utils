# coding=utf-8

"""
Tests for an md_utils program
"""
import os
import unittest
from md_utils.fill_tpl import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
import logging

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'


DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'fill_tpl')

PAR_INI = os.path.join(SUB_DATA_DIR, 'make_par.ini')
PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_test.par')
GOOD_PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_test_good.par')


class TestMakeParFailWell(unittest.TestCase):
    # These tests only check for (hopefully) helpful messages
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)


class TestMakePar(unittest.TestCase):
    def testRep(self):
        try:
            main(["-c", PAR_INI])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
