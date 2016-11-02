# coding=utf-8

"""
Tests for an md_utils program
"""
import os
import unittest
from md_utils.converge_evb_par import main, PAR_FILE_NAME, TRIAL_NAME
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
import logging

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'converge_evb_par')
FILL_DIR = os.path.join(DATA_DIR, 'fill_tpl')

CONV_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par.ini')

PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_hm_maupin_gauss_3.5.par')
COPY_PAR = os.path.join(DATA_DIR, 'evb_viib0.0_viilb1.00.par')
GOOD_PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_hm_maupin_gauss_3.5_good.par')
ALT_PAR_FNAME = os.path.join(SUB_DATA_DIR, 'evb.par')

# PAR_NO_NEW_FILE_NAME_INI = os.path.join(SUB_DATA_DIR, 'no_new_fname.ini')
# PAR_FNAME = 'evb_test.par'
# PAR_OUT = os.path.join(SUB_DATA_DIR, PAR_FNAME)
# GOOD_PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_test_good.par')
#
# PAR_ONE_MULTI_INI = os.path.join(SUB_DATA_DIR, 'make_one_multi_par.ini')
# PAR_TWO_MULTI_INI = os.path.join(SUB_DATA_DIR, 'make_multi_par.ini')
# MULTI_PAR_OUT1 = os.path.join(SUB_DATA_DIR, 'evb_viib0.0_viilb1.00.par')
# MULTI_PAR_OUT2 = os.path.join(SUB_DATA_DIR, 'evb_viib-0.5_viilb1.00.par')
# MULTI_PAR_OUT3 = os.path.join(SUB_DATA_DIR, 'evb_viib-1.0_viilb1.00.par')
# MULTI_PAR_OUT4 = os.path.join(SUB_DATA_DIR, 'evb_viib0.0_viilb5.00.par')
# MULTI_PAR_OUT5 = os.path.join(SUB_DATA_DIR, 'evb_viib-0.5_viilb5.00.par')
# MULTI_PAR_OUT6 = os.path.join(SUB_DATA_DIR, 'evb_viib-1.0_viilb5.00.par')
# MULTI_OUT_FILES = [MULTI_PAR_OUT1, MULTI_PAR_OUT2, MULTI_PAR_OUT3,
#                    MULTI_PAR_OUT4, MULTI_PAR_OUT5, MULTI_PAR_OUT6, ]
# GOOD_MULTI_PAR_OUT1 = os.path.join(SUB_DATA_DIR, 'evb_test_multi1_good.par')
# GOOD_MULTI_PAR_OUT3 = os.path.join(SUB_DATA_DIR, 'evb_test_multi3_good.par')
# GOOD_MULTI_PAR_OUT4 = os.path.join(SUB_DATA_DIR, 'evb_test_multi4_good.par')
# GOOD_MULTI_PAR_OUT5 = os.path.join(SUB_DATA_DIR, 'evb_test_multi5_good.par')
# GOOD_MULTI_PAR_OUT6 = os.path.join(SUB_DATA_DIR, 'evb_test_multi6_good.par')
#
# PAR_EQ_INI = os.path.join(SUB_DATA_DIR, 'make_eq_par.ini')
# PAR_EQ_WRONG_ORDER_INI = os.path.join(SUB_DATA_DIR, 'make_eq_par_wrong_order.ini')
# PAR_EQ_MISS_PARAM_INI = os.path.join(SUB_DATA_DIR, 'make_eq_par_missing_param.ini')

# for testing to fail well
MISSING_TRIAL_NAME_KEY_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_missing_key_in_trial_name.ini')
MISSING_TRIAL_NAME_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_no_trial_name.ini')
MISSING_TPL_KEY_INI = os.path.join(SUB_DATA_DIR, 'missing_tpl_key.ini')
MISSING_TPL_INI = os.path.join(SUB_DATA_DIR, 'missing_tpl.ini')
MISSING_PAR_NAME = os.path.join(SUB_DATA_DIR, 'missing_new_par_name.ini')
TPL_KEY_IN_MAIN_INI = os.path.join(FILL_DIR, 'tpl_key_in_main.ini')
VAL_BEFORE_SECTION_INI = os.path.join(FILL_DIR, 'no_initial_section.ini')
MISSING_MAIN_INI = os.path.join(FILL_DIR, 'missing_main.ini')
EXTRA_SEC_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_extra_section.ini')


class TestMainFailWell(unittest.TestCase):
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
        test_input = ["-c", MISSING_TPL_KEY_INI]
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
        test_input = ["-c", MISSING_PAR_NAME]
        main(test_input)
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue(PAR_FILE_NAME in output)

    def testTplKeyInMain(self):
        # aim for a helpful message if the template key is in main
        test_input = ["-c", TPL_KEY_IN_MAIN_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('Unexpected key' in output)

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

    def testNoTrialName(self):
        # catch an error if the program finds an unexpected section
        test_input = ["-c", MISSING_TRIAL_NAME_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Missing key name 'trial_name'" in output)
        silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testMissingTrialNameKey(self):
        # catch an error if the program finds an unexpected section
        test_input = ["-c", MISSING_TRIAL_NAME_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue(TRIAL_NAME in output)
        silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    #
    # def testMakeParMissingKeyFileName(self):
    #     test_input = ["-c", PAR_NO_NEW_FILE_NAME_INI, "-f", '{ghost}.par']
    #     if logger.isEnabledFor(logging.DEBUG):
    #         main(test_input)
    #     with capture_stderr(main, test_input) as output:
    #         self.assertTrue('required for filled template file name' in output)
    #
    # def testMakeParEqWrongOrder(self):
    #     test_input = ["-c", PAR_EQ_WRONG_ORDER_INI]
    #     if logger.isEnabledFor(logging.DEBUG):
    #         main(test_input)
    #     with capture_stderr(main, test_input) as output:
    #         self.assertTrue('Check order' in output)
    #
    # def testMakeParEqMissingParam(self):
    #     test_input = ["-c", PAR_EQ_MISS_PARAM_INI]
    #     if logger.isEnabledFor(logging.DEBUG):
    #         main(test_input)
    #     with capture_stderr(main, test_input) as output:
    #         self.assertTrue('Missing parameter value' in output)


class TestMain(unittest.TestCase):
    def testMakePar(self):
        # For this test, there is exactly one value provided for each parameter
        try:
            silent_remove(PAR_OUT, COPY_PAR)
            main(["-c", CONV_INI])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
            self.assertFalse(diff_lines(COPY_PAR, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(COPY_PAR, disable=DISABLE_REMOVE)

    def testMakeParCommandLine(self):
        # as in testMakePar, but specifying the created file name from the command line
        try:
            main(["-c", CONV_INI, "-f", ALT_PAR_FNAME])
            self.assertFalse(diff_lines(ALT_PAR_FNAME, GOOD_PAR_OUT))
        finally:
            silent_remove(ALT_PAR_FNAME, disable=DISABLE_REMOVE)
            silent_remove(COPY_PAR, disable=DISABLE_REMOVE)
