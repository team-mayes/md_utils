# coding=utf-8

"""
Tests for fitevb_setup.py.
"""
import os
import unittest
import logging
from md_utils.fitevb_setup import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

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

MISS_KEY_INFO_PATH = os.path.join(SUB_DATA_DIR, 'fitevb_setup_missing_keyinfo.ini')

PT_INI = os.path.join(SUB_DATA_DIR, 'fitevb_setup_pt.ini')


class TestFitEVBSetupFailWell(unittest.TestCase):
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoIni(self):
        test_input = []
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments:" in output)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problems reading file: Could not read file" in output)

    def testMissingSection(self):
        test_input = ["-c", MISS_SEC_INI_PATH, "-f", FITEVB_OUTPUT_PATH]
        with capture_stderr(main, test_input) as output:
            self.assertTrue("missing section" in output)

    def testMissingParam(self):
        test_input = ["-c", MISS_PARAM_INI_PATH, "-f", FITEVB_OUTPUT_PATH, ]
        with capture_stderr(main, test_input) as output:
            self.assertTrue("missing parameter" in output)

    def testMissingInputFile(self):
        with capture_stderr(main, ["-c", INI_PATH, ]) as output:
            self.assertTrue("Problems reading " in output)

    def testInputFile(self):
        test_input = ["-c", MISS_KEY_INFO_PATH, "-f", FITEVB_OUTPUT_PATH]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("expected comma-separated numerical lower range" in output)


class TestFitEVBSetup(unittest.TestCase):
    def testNoViiFit(self):
        try:
            main(["-c", INI_PATH, "-f", FITEVB_OUTPUT_PATH])
            self.assertFalse(diff_lines(DEF_OUT_PATH, GOOD_NO_VII_FIT_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH, disable=DISABLE_REMOVE)

    def testViiFit(self):
        try:
            main(["-c", INI_PATH, "-f", FITEVB_OUTPUT_PATH, "-v", "True"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, GOOD_VII_FIT_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH, disable=DISABLE_REMOVE)

    def testPTFit(self):
        test_input = ["-c", PT_INI, "-f", FITEVB_OUTPUT_PATH]
        main(test_input)
        # try:
        #     main(["-c", PT_INI, "-f", FITEVB_OUTPUT_PATH])
        #     self.assertFalse(diff_lines(DEF_OUT_PATH, GOOD_VII_FIT_OUT_PATH))
        # finally:
        #     silent_remove(DEF_OUT_PATH, disable=DISABLE_REMOVE)
