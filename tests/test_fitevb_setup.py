# coding=utf-8

"""
Tests for fitevb_setup.py.
"""
import os
import unittest

from md_utils import fitevb_setup
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.dirname(TEST_DIR)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'fitevb')

FITEVB_OUTPUT_PATH = os.path.join(SUB_DATA_DIR, 'fit.best')

INI_PATH = os.path.join(SUB_DATA_DIR, 'fitevb_setup.ini')
MISS_SEC_INI_PATH = os.path.join(SUB_DATA_DIR, 'fitevb_setup_missing_section.ini')
MISS_PARAM_INI_PATH = os.path.join(SUB_DATA_DIR, 'fitevb_setup_missing_param.ini')

GOOD_VII_FIT_OUT_PATH = os.path.join(SUB_DATA_DIR, 'fit_vii_good.inp')
GOOD_NO_VII_FIT_OUT_PATH = os.path.join(SUB_DATA_DIR, 'fit_not_vii_good.inp')
# noinspection PyUnresolvedReferences
DEF_OUT_PATH = os.path.join(MAIN_DIR, 'fit.inp')


class TestFitEVBSetup(unittest.TestCase):

    def testNoIni(self):
        with capture_stdout(fitevb_setup.main,[]) as output:
            self.assertTrue("optional arguments:" in output)
        with capture_stderr(fitevb_setup.main,[]) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)

    def testNoViiFit(self):
        try:
            fitevb_setup.main(["-c", INI_PATH, "-f", FITEVB_OUTPUT_PATH])
            self.assertFalse(diff_lines(DEF_OUT_PATH, GOOD_NO_VII_FIT_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testViiFit(self):
        try:
            fitevb_setup.main(["-c", INI_PATH, "-f", FITEVB_OUTPUT_PATH, "-v", "True"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, GOOD_VII_FIT_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testMissingSection(self):
        with capture_stderr(fitevb_setup.main,["-c", MISS_SEC_INI_PATH, "-f", FITEVB_OUTPUT_PATH, ]) as output:
            self.assertTrue("missing section" in output)

    def testMissingParam(self):
        with capture_stderr(fitevb_setup.main,["-c", MISS_PARAM_INI_PATH, "-f", FITEVB_OUTPUT_PATH, ]) as output:
            self.assertTrue("missing parameter" in output)

    def testInputFile(self):
        with capture_stderr(fitevb_setup.main,["-c", INI_PATH, ]) as output:
            self.assertTrue("Problems reading " in output)
