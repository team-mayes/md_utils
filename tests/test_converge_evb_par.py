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

MAIN_DIR = os.path.join(os.path.dirname(__file__), os.path.pardir)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'converge_evb_par')
FILL_DIR = os.path.join(DATA_DIR, 'fill_tpl')

CONV_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par.ini')
CONV_ALT_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_alt.ini')
PAR_INI = os.path.join(SUB_DATA_DIR, 'evb_par.ini')
CONV_MAX_ITER_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_max_iters.ini')
CONV_MAX_STEP_SIZE_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_max_step_size.ini')
COPY_OUTPUT_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_multi_par.ini')
MAX_MIN_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_multi_par_min_val.ini')
DIRS_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_multi_par_initial_dirs.ini')
REPEAT_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_multi_par_repeat_min.ini')
TRIANGLE_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_multi_par_triangle.ini')

CONV_NM_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_so.ini')
CONV_NM_MULTI_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_so_multi.ini')
CONV_NOT_TESTED_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_not_tested_method.ini')
CONV_HOP_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_basin_hop.ini')
CONV_HOP_MIN_MAX_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_basin_hop_min_max.ini')
BIN_HOP_RESULT_SUM = os.path.join(SUB_DATA_DIR, 'bin_hop_results.csv')
GOOD_BIN_HOP_RESULT_SUM = os.path.join(SUB_DATA_DIR, 'bin_hop_results_good.csv')
BEST_PARAMS = os.path.join(SUB_DATA_DIR, 'best_params.txt')
GOOD_BEST_PARAMS = os.path.join(SUB_DATA_DIR, 'best_params_good.txt')

PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_hm_maupin_gauss_3.5.par')
COPY_PAR = os.path.join(DATA_DIR, 'evb_viib0.0_viilb1.0.par')
GOOD_PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_hm_maupin_gauss_3.5_good.par')
GOOD_PAR_OUT2 = os.path.join(SUB_DATA_DIR, 'evb_hm_maupin_gauss_3.5_good2.par')
GOOD_MAX_MIN_PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_hm_maupin_gauss_3.5_min_max_good.par')
ALT_PAR_FNAME = os.path.join(SUB_DATA_DIR, 'evb.par')
SCRIPT_OUT = os.path.join(MAIN_DIR, 'script_output.txt')
SCRIPT_COPY_OUT = os.path.join(DATA_DIR, 'script_viib0.0_viilb1.0.txt')
GOOD_SCRIPT_OUT = os.path.join(SUB_DATA_DIR, 'script_out_good.txt')
RESULT_SUM = os.path.join(MAIN_DIR, 'vii0_vij0_gamma.csv')
GOOD_RESULT_SUM = os.path.join(SUB_DATA_DIR, 'result_sum_good.csv')
RESID_PAR_OUT = os.path.join(DATA_DIR, 'evb_resid8.0_viilb1.0.par')
OTHER_RESID_NAMES = ['evb_resid8.145898_viilb1.0.par',
                     'evb_resid8.381966_viilb1.0.par',
                     'evb_resid9.0_viilb1.0.par',
                     'evb_resid10.618034_viilb1.0.par',
                     'evb_resid10212.284784_viilb1.0.par',
                     'evb_resid26723.164692_viilb1.0.par',
                     'evb_resid76948.755062_viilb1.0.par',
                     'evb_resid77849.0_viilb1.0.par',
                     'evb_resid78408.0_viilb1.0.par']

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
WRONG_MAX_ITER_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_wrong_max_iter.ini')
MISSING_EQ_KEY_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_missing_eq_key.ini')
WRONG_EQ_ORDER_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_wrong_eq_order.ini')
TOO_MANY_PARAM_VALS_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_multi_par_vals.ini')
MISSING_BASH_SCRIPT_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_missing_bash.ini')
MISSING_RESULT_FNAME_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_missing_output_fname.ini')
NON_FLOAT_MIN_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_nonfloat_min.ini')
TOO_MANY_MAX_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_too_many_max.ini')
NON_FLOAT_DIR_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_multi_par_bad_dirs.ini')
CONV_HOP_MAX_MIN_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_basin_hop_switch_min_max.ini')
CONV_HOP_NONFLOAT_MAX_INI = os.path.join(SUB_DATA_DIR, 'conv_evb_par_basin_hop_nonfloat_max.ini')


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

    def testMissingConfig(self):
        test_input = ["-c", 'ghost']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not read file" in output)

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
        silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)

    def testMissingTrialNameKey(self):
        test_input = ["-c", MISSING_TRIAL_NAME_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue(TRIAL_NAME in output)
        silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)
        silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testNonIntMaxIter(self):
        test_input = ["-c", WRONG_MAX_ITER_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("invalid literal for int()" in output)

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

    def testTwoParamVals(self):
        test_input = ["-c", TOO_MANY_PARAM_VALS_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("3 values were found" in output)

    def testMissingBashScript(self):
        test_input = ["-c", MISSING_BASH_SCRIPT_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Missing file" in output)

    def testMissingResultFileName(self):
        test_input = ["-c", MISSING_RESULT_FNAME_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("bash driver output" in output)

    def testNonfloatMin(self):
        test_input = ["-c", NON_FLOAT_MIN_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("convert string" in output)

    def testTooManyMax(self):
        test_input = ["-c", TOO_MANY_MAX_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Expected" in output)

    def testNonFloatDir(self):
        test_input = ["-c", NON_FLOAT_DIR_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("float" in output)

    def testBasinHopMaxMin(self):
        # test catching min greater than max
        test_input = ["-c", CONV_HOP_MAX_MIN_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("is not less than" in output)

    def testBasinHopNonFloatMax(self):
        # test catching min greater than max
        test_input = ["-c", CONV_HOP_NONFLOAT_MAX_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("could not convert string" in output)


class TestMain(unittest.TestCase):
    def testMakeParStartLow(self):
        # For this test, there is exactly one value provided for each parameter, and x_0 is too low
        silent_remove(PAR_OUT)
        silent_remove(COPY_PAR)
        try:
            main(["-c", CONV_INI])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT2))
            self.assertFalse(diff_lines(COPY_PAR, GOOD_PAR_OUT2))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(COPY_PAR, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)

    def testMakeParStartHigh(self):
        # Testing that starting from an x_0 too high still ends at the same answer
        # Also check specifying par file name in command line; should overwrite what is in the config file
        try:
            silent_remove(ALT_PAR_FNAME)
            main(["-c", CONV_ALT_INI, "-f", ALT_PAR_FNAME])
            self.assertFalse(diff_lines(ALT_PAR_FNAME, GOOD_PAR_OUT2))
            self.assertFalse(diff_lines(RESID_PAR_OUT, GOOD_PAR_OUT2))
        finally:
            silent_remove(ALT_PAR_FNAME, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)
            silent_remove(RESID_PAR_OUT, disable=DISABLE_REMOVE)
            for file_name in OTHER_RESID_NAMES:
                silent_remove(os.path.join(DATA_DIR, file_name), disable=DISABLE_REMOVE)

    def testNoOpt(self):
        # Testing that will run without any params specified to be optimized
        silent_remove(PAR_OUT)
        test_input = ["-c", PAR_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stderr(main, test_input) as output:
                self.assertTrue("No parameters will be optimized" in output)
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT2))
            self.assertFalse(diff_lines(COPY_PAR, GOOD_PAR_OUT2))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(COPY_PAR, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)

    def testMaxIterNum(self):
        # Specified a small number of iterations
        test_input = ["-c", CONV_MAX_ITER_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue("Maximum number of function evaluations has been exceeded" in output)
            diffs = diff_lines(PAR_OUT, GOOD_PAR_OUT2)
            self.assertEquals(len(diffs), 2)
            self.assertEquals('- -0.000000    : constant Vii', diffs[0])
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)

    def testCopyOutput(self):
        # Stop based on step size; multiple variables
        try:
            # since we backup RESULT_SUM, start by removing it so we don't accidentally make a copy
            silent_remove(RESULT_SUM)
            test_input = ["-c", COPY_OUTPUT_INI]
            main(test_input)
            self.assertFalse(diff_lines(SCRIPT_OUT, GOOD_SCRIPT_OUT))
            self.assertFalse(diff_lines(SCRIPT_COPY_OUT, GOOD_SCRIPT_OUT))
            self.assertFalse(diff_lines(RESULT_SUM, GOOD_RESULT_SUM))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(COPY_PAR, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_COPY_OUT, disable=DISABLE_REMOVE)
            silent_remove(RESULT_SUM, disable=DISABLE_REMOVE)

    def testMaxMin(self):
        # Stop based on step size
        try:
            test_input = ["-c", MAX_MIN_INI]
            main(test_input)
            self.assertFalse(diff_lines(PAR_OUT, GOOD_MAX_MIN_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)

    def testInitialDirections(self):
        # Start multi-variable
        test_input = ["-c", DIRS_INI]
        try:
            silent_remove(BEST_PARAMS)
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                # this option reduced the function calls by 1 (19 to 18)
                self.assertTrue("Function evaluations: 223" in output)
                self.assertFalse(diff_lines(BEST_PARAMS, GOOD_BEST_PARAMS))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)
            silent_remove(BEST_PARAMS, disable=DISABLE_REMOVE)

    def testNonTestedMethod(self):
        # Try alternate minimization method
        try:
            test_input = ["-c", CONV_NOT_TESTED_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stderr(main, test_input) as output:
                self.assertTrue("Only the following optimization methods" in output)
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)

    def testNelderMead(self):
        # Try alternate minimization method
        try:
            test_input = ["-c", CONV_NM_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("Function evaluations: 24" in output)
                self.assertTrue("vii_0:    0.000000" in output)
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)

    def testNelderMeadMultiVar(self):
        # Try alternate minimization method for multiple variable. Did worse than Powell for multiple functions
        # Results from Powell are:
        # Current function value: 0.000000
        # Iterations: 10
        # Function evaluations: 242
        # Optimized parameters:
        # vii_0 = 2.000000
        # vij_0 = 0.000000
        # gamma = -2.000000
        try:
            test_input = ["-c", CONV_NM_MULTI_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("Current function value: 6.192328" in output)
                self.assertTrue("Iterations: 29" in output)
                self.assertTrue("Function evaluations: 56" in output)
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)

    def testBasinHop(self):
        # Try hopping + minimization
        try:
            test_input = ["-c", CONV_HOP_INI]
            silent_remove(BIN_HOP_RESULT_SUM)
            main(test_input)
            self.assertFalse(diff_lines(BIN_HOP_RESULT_SUM, GOOD_BIN_HOP_RESULT_SUM))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)
            silent_remove(BIN_HOP_RESULT_SUM, disable=DISABLE_REMOVE)

    def testBasinHopBounds(self):
        # Try hopping + minimization
        try:
            test_input = ["-c", CONV_HOP_MIN_MAX_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("success condition satisfied. Number of function calls: 83" in output)
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)

    def testRepeatMin(self):
        # Test repeating minimization and removing duplicate opt_params
        test_input = ["-c", REPEAT_INI]
        try:
            silent_remove(BEST_PARAMS)
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("Optimization terminated successfully. Completed 2 of 3 minimization cycles\n"
                                in output)
                self.assertFalse(diff_lines(BEST_PARAMS, GOOD_BEST_PARAMS))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)
            silent_remove(BEST_PARAMS, disable=DISABLE_REMOVE)

    def testTriangleMin(self):
        # Test stepwise minimization
        test_input = ["-c", TRIANGLE_INI]
        try:
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("Resid:    4.000000 for parameters:    0.000000,   2.000000\n" in output)
                self.assertTrue("Resid:    0.000000 for parameters:    0.000000,   2.000000,  -2.000000\n" in output)
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
            silent_remove(SCRIPT_OUT, disable=DISABLE_REMOVE)
