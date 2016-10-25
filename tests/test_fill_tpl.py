# coding=utf-8

"""
Tests for an md_utils program
"""
import os
import unittest
from md_utils.fill_tpl import main, FILLED_TPL_FNAME
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'


DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'fill_tpl')

PAR_INI = os.path.join(SUB_DATA_DIR, 'make_par.ini')
PAR_NO_NEW_FILE_NAME_INI = os.path.join(SUB_DATA_DIR, 'no_new_fname.ini')
PAR_FNAME = 'evb_test.par'
PAR_OUT = os.path.join(SUB_DATA_DIR, PAR_FNAME)
GOOD_PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_test_good.par')

PAR_MULTI_INI = os.path.join(SUB_DATA_DIR, 'make_multi_par.ini')
MULTI_PAR_OUT1 = os.path.join(SUB_DATA_DIR, 'evb_viib0.0_viilb1.00.par')
MULTI_PAR_OUT2 = os.path.join(SUB_DATA_DIR, 'evb_viib-0.5_viilb1.00.par')
MULTI_PAR_OUT3 = os.path.join(SUB_DATA_DIR, 'evb_viib-1.0_viilb1.00.par')
MULTI_PAR_OUT4 = os.path.join(SUB_DATA_DIR, 'evb_viib0.0_viilb5.00.par')
MULTI_PAR_OUT5 = os.path.join(SUB_DATA_DIR, 'evb_viib-0.5_viilb5.00.par')
MULTI_PAR_OUT6 = os.path.join(SUB_DATA_DIR, 'evb_viib-1.0_viilb5.00.par')
MULTI_OUT_FILES = [MULTI_PAR_OUT1, MULTI_PAR_OUT2, MULTI_PAR_OUT3,
                   MULTI_PAR_OUT4, MULTI_PAR_OUT5, MULTI_PAR_OUT6, ]
GOOD_MULTI_PAR_OUT1 = os.path.join(SUB_DATA_DIR, 'evb_test_multi1_good.par')
GOOD_MULTI_PAR_OUT3 = os.path.join(SUB_DATA_DIR, 'evb_test_multi3_good.par')
GOOD_MULTI_PAR_OUT4 = os.path.join(SUB_DATA_DIR, 'evb_test_multi4_good.par')
GOOD_MULTI_PAR_OUT5 = os.path.join(SUB_DATA_DIR, 'evb_test_multi5_good.par')
GOOD_MULTI_PAR_OUT6 = os.path.join(SUB_DATA_DIR, 'evb_test_multi6_good.par')

PAR_EQ_INI = os.path.join(SUB_DATA_DIR, 'make_eq_par.ini')

# for testing to fail well
MISSING_DEF_TPL_INI = os.path.join(SUB_DATA_DIR, 'missing_def_tpl.ini')
MISSING_TPL_INI = os.path.join(SUB_DATA_DIR, 'missing_tpl.ini')
MISSING_TPL_KEY_INI = os.path.join(SUB_DATA_DIR, 'missing_tpl_key.ini')
TPL_KEY_IN_MAIN_INI = os.path.join(SUB_DATA_DIR, 'tpl_key_in_main.ini')
VAL_BEFORE_SECTION_INI = os.path.join(SUB_DATA_DIR, 'no_initial_section.ini')
MISSING_MAIN_INI = os.path.join(SUB_DATA_DIR, 'missing_main.ini')
EXTRA_SEC_INI = os.path.join(SUB_DATA_DIR, 'extra_section.ini')


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

    def testMissingDefaultTpl(self):
        test_input = ["-c", MISSING_DEF_TPL_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("default template file" in output)

    def testMissingTpl(self):
        test_input = ["-c", MISSING_TPL_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("template file specified" in output)

    def testMissingFilledTplName(self):
        # new file name not specified by either config file or command line
        test_input = ["-c", PAR_NO_NEW_FILE_NAME_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue(FILLED_TPL_FNAME in output)

    def testTplKeyInMain(self):
        # aim for a helpful message if the template key is in main
        test_input = ["-c", TPL_KEY_IN_MAIN_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('Unexpected key' in output)

    def testMissingTplKey(self):
        # make sure it gracefully fails when a template key is missing
        test_input = ["-c", MISSING_TPL_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('required for template file' in output)

    def testValBeforeSection(self):
        # make sure it gracefully fails when a template key is missing
        test_input = ["-c", VAL_BEFORE_SECTION_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('must start with' in output)

    def testMissingMain(self):
        # make sure it gracefully fails when a template key is missing
        test_input = ["-c", MISSING_MAIN_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("missing the required 'main' section" in output)

    def testExtraSection(self):
        # catch an error if the program finds an unexpected section
        test_input = ["-c", EXTRA_SEC_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('not one of the valid section names' in output)

    def testMakeParMissingKeyFileName(self):
        test_input = ["-c", PAR_NO_NEW_FILE_NAME_INI, "-f", '{ghost}.par']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('required for filled template file name' in output)


class TestMain(unittest.TestCase):
    def testMakePar(self):
        try:
            silent_remove(PAR_OUT)
            main(["-c", PAR_INI])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testMakeParCommandLine(self):
        try:
            silent_remove(PAR_OUT)
            main(["-c", PAR_NO_NEW_FILE_NAME_INI, "-f", PAR_FNAME])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testMakeMultiPar(self):
        try:
            for o_file in MULTI_OUT_FILES:
                silent_remove(o_file)
            main(["-c", PAR_MULTI_INI])
            self.assertFalse(diff_lines(MULTI_PAR_OUT1, GOOD_MULTI_PAR_OUT1))
            # self.assertFalse(diff_lines(MULTI_PAR_OUT2, GOOD_PAR_OUT))
            # self.assertFalse(diff_lines(MULTI_PAR_OUT3, GOOD_MULTI_PAR_OUT3))
        finally:
            for o_file in MULTI_OUT_FILES:
                silent_remove(o_file, disable=DISABLE_REMOVE)
