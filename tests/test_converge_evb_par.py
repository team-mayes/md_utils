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
CONV_ALT_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_alt.ini')
PAR_INI = os.path.join(SUB_DATA_DIR, 'evb_par.ini')
CONV_MAX_ITER_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_max_steps.ini')
CONV_MAX_STEP_SIZE_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_max_step_size.ini')

PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_hm_maupin_gauss_3.5.par')
COPY_PAR = os.path.join(DATA_DIR, 'evb_viib0.0_viilb1.00.par')
GOOD_PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_hm_maupin_gauss_3.5_good.par')
ALT_PAR_FNAME = os.path.join(SUB_DATA_DIR, 'evb.par')

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
WRONG_STEP_ORDER_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_wrong_step_sizes.ini')
MISSING_STEP_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_missing_step.ini')
MISSING_EQ_KEY_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_missing_eq_key.ini')
WRONG_EQ_ORDER_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_wrong_eq_order.ini')


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
        test_input = ["-c", MISSING_TRIAL_NAME_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue(TRIAL_NAME in output)
        silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testWrongStepSizeOrder(self):
        test_input = ["-c", WRONG_STEP_ORDER_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("smaller" in output)

    def testMissingStep(self):
        test_input = ["-c", MISSING_STEP_INI]
        main(test_input)
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("2 values were found" in output)

    def testMissingEqKey(self):
        test_input = ["-c", MISSING_EQ_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("needed to evaluate" in output)

    def testWrongEqOrder(self):
        test_input = ["-c", WRONG_EQ_ORDER_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not evaluate" in output)


class TestMain(unittest.TestCase):
    def testMakeParStartLow(self):
        # For this test, there is exactly one value provided for each parameter, and x_0 is too low
        try:
            silent_remove(PAR_OUT, COPY_PAR)
            main(["-c", CONV_INI])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
            self.assertFalse(diff_lines(COPY_PAR, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(COPY_PAR, disable=DISABLE_REMOVE)
            pass

    def testMakeParStartHigh(self):
        # Testing that starting from an x_0 too high still ends at the same answer
        try:
            silent_remove(PAR_OUT)
            main(["-c", CONV_ALT_INI])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testNoOpt(self):
        # Testing that will run without any params specified to be optimized
        silent_remove(PAR_OUT)
        test_input = ["-c", PAR_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stderr(main, test_input) as output:
                self.assertTrue("No parameters will be optimized" in output)
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testMaxIters(self):
        # Specified a small number of iterations
        try:
            main(["-c", CONV_MAX_ITER_INI])
            diffs = diff_lines(PAR_OUT, GOOD_PAR_OUT)
            self.assertEquals(len(diffs), 2)
            self.assertEquals('- -300.0       : constant Vii', diffs[0])
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testMaxStepSize(self):
        # Stop based on step size
        try:
            test_input = ["-c", CONV_MAX_STEP_SIZE_INI]
            with capture_stdout(main, test_input) as output:
                self.assertTrue("min step size" in output)
            diffs = diff_lines(PAR_OUT, GOOD_PAR_OUT)
            self.assertEquals(len(diffs), 2)
            self.assertEquals('- -293.75      : constant Vii', diffs[0])
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
