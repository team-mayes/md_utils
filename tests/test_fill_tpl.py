# coding=utf-8

"""
Tests for an md_utils program
"""
import os
import unittest
from md_utils.fill_tpl import main, FILLED_TPL_FNAME
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
import logging

# logging.basicConfig(level=logging.DEBUG) # uncomment this for debug mode
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

PAR_ONE_MULTI_INI = os.path.join(SUB_DATA_DIR, 'make_one_multi_par.ini')
PAR_TWO_MULTI_INI = os.path.join(SUB_DATA_DIR, 'make_multi_par.ini')
MULTI_PAR_OUT1 = os.path.join(SUB_DATA_DIR, 'evb_viib0.0_viilb1.0.par')
MULTI_PAR_OUT2 = os.path.join(SUB_DATA_DIR, 'evb_viib-0.5_viilb1.0.par')
MULTI_PAR_OUT3 = os.path.join(SUB_DATA_DIR, 'evb_viib-1.0_viilb1.0.par')
MULTI_PAR_OUT4 = os.path.join(SUB_DATA_DIR, 'evb_viib0.0_viilb5.0.par')
MULTI_PAR_OUT5 = os.path.join(SUB_DATA_DIR, 'evb_viib-0.5_viilb5.0.par')
MULTI_PAR_OUT6 = os.path.join(SUB_DATA_DIR, 'evb_viib-1.0_viilb5.0.par')
MULTI_OUT_FILES = [MULTI_PAR_OUT1, MULTI_PAR_OUT2, MULTI_PAR_OUT3,
                   MULTI_PAR_OUT4, MULTI_PAR_OUT5, MULTI_PAR_OUT6, ]
GOOD_MULTI_PAR_OUT1 = os.path.join(SUB_DATA_DIR, 'evb_test_multi1_good.par')
GOOD_MULTI_PAR_OUT3 = os.path.join(SUB_DATA_DIR, 'evb_test_multi3_good.par')
GOOD_MULTI_PAR_OUT4 = os.path.join(SUB_DATA_DIR, 'evb_test_multi4_good.par')
GOOD_MULTI_PAR_OUT5 = os.path.join(SUB_DATA_DIR, 'evb_test_multi5_good.par')
GOOD_MULTI_PAR_OUT6 = os.path.join(SUB_DATA_DIR, 'evb_test_multi6_good.par')

PAR_EQ_INI = os.path.join(SUB_DATA_DIR, 'make_eq_par.ini')
PAR_EQ_WRONG_ORDER_INI = os.path.join(SUB_DATA_DIR, 'make_eq_par_wrong_order.ini')
PAR_EQ_MISS_PARAM_INI = os.path.join(SUB_DATA_DIR, 'make_eq_par_missing_param.ini')

PROD_GPU_JOB_INI = os.path.join(SUB_DATA_DIR, 'make_prod_gpu_job.ini')
PROD_GPU_JOB_OUT = os.path.join(SUB_DATA_DIR, 'test.job')
GOOD_PROD_GPU_JOB_OUT = os.path.join(SUB_DATA_DIR, 'production_gpu_good.job')
PROD_GPU_INP_INI = os.path.join(SUB_DATA_DIR, 'make_prod_gpu_inp.ini')
PROD_GPU_INP_OUT = os.path.join(SUB_DATA_DIR, 'test.inp')
GOOD_PROD_GPU_INP_OUT = os.path.join(SUB_DATA_DIR, 'production_gpu_good.inp')
PROD_GPU_JOB_INP_INI = os.path.join(SUB_DATA_DIR, 'make_prod_gpu.ini')
PROD_CPU_JOB_OUT = os.path.join(SUB_DATA_DIR, 'test.pbs')
PROD_CPU_INP_OUT = os.path.join(SUB_DATA_DIR, 'test.inp')
PROD_CPU_JOB_INP_INI = os.path.join(SUB_DATA_DIR, 'make_prod_cpu.ini')
GOOD_PROD_CPU_INP_OUT = os.path.join(SUB_DATA_DIR, 'production_cpu_good.inp')
GOOD_PROD_CPU_JOB_OUT = os.path.join(SUB_DATA_DIR, 'production_cpu_good.pbs')

AMD_GPU_JOB_INP_INI = os.path.join(SUB_DATA_DIR, 'make_amd_gpu.ini')
AMD_GPU_JOB_OUT = os.path.join(SUB_DATA_DIR, 'aMD.2.job')
AMD_GPU_INP_OUT = os.path.join(SUB_DATA_DIR, 'aMD.2.inp')
GOOD_AMD_GPU_INP_OUT = os.path.join(SUB_DATA_DIR, 'aMD_good.inp')
GOOD_AMD_GPU_JOB_OUT = os.path.join(SUB_DATA_DIR, 'aMD_good.job')

# for testing to fail well
MISSING_DEF_TPL_INI = os.path.join(SUB_DATA_DIR, 'missing_def_tpl.ini')
MISSING_TPL_INI = os.path.join(SUB_DATA_DIR, 'missing_tpl.ini')
MISSING_TPL_KEY_INI = os.path.join(SUB_DATA_DIR, 'missing_tpl_key.ini')
TPL_KEY_IN_MAIN_INI = os.path.join(SUB_DATA_DIR, 'tpl_key_in_main.ini')
VAL_BEFORE_SECTION_INI = os.path.join(SUB_DATA_DIR, 'no_initial_section.ini')
MISSING_MAIN_INI = os.path.join(SUB_DATA_DIR, 'missing_main.ini')
EXTRA_SEC_INI = os.path.join(SUB_DATA_DIR, 'extra_section.ini')
TPL_MISMATCH = os.path.join(SUB_DATA_DIR, 'tpl_mismatch.ini')


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

    def testMakeParEqWrongOrder(self):
        test_input = ["-c", PAR_EQ_WRONG_ORDER_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('Check order' in output)

    def testMakeParEqMissingParam(self):
        test_input = ["-c", PAR_EQ_MISS_PARAM_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('Missing parameter value' in output)

    def testMakeParTplNumberMismatch(self):
        test_input = ["-c", TPL_MISMATCH]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('The same number of' in output)


class TestMain(unittest.TestCase):
    def testMakePar(self):
        # For this test, there is exactly one value provided for each parameter
        try:
            silent_remove(PAR_OUT)
            main(["-c", PAR_INI])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testMakeParCommandLine(self):
        # as in testMakePar, but specifying the created file name from the command line
        try:
            silent_remove(PAR_OUT)
            main(["-c", PAR_NO_NEW_FILE_NAME_INI, "-f", PAR_FNAME])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testMakeOneMultiPar(self):
        # Now, one parameter has multiple values
        try:
            for o_file in MULTI_OUT_FILES:
                silent_remove(o_file)
            main(["-c", PAR_ONE_MULTI_INI])
            self.assertFalse(diff_lines(MULTI_PAR_OUT1, GOOD_MULTI_PAR_OUT1))
            self.assertFalse(diff_lines(MULTI_PAR_OUT2, GOOD_PAR_OUT))
            self.assertFalse(diff_lines(MULTI_PAR_OUT3, GOOD_MULTI_PAR_OUT3))
        finally:
            for o_file in MULTI_OUT_FILES:
                silent_remove(o_file, disable=DISABLE_REMOVE)

    def testMakeTwoMultiPar(self):
        try:
            for o_file in MULTI_OUT_FILES:
                silent_remove(o_file)
            main(["-c", PAR_TWO_MULTI_INI])
            self.assertFalse(diff_lines(MULTI_PAR_OUT1, GOOD_MULTI_PAR_OUT1))
            self.assertFalse(diff_lines(MULTI_PAR_OUT2, GOOD_PAR_OUT))
            self.assertFalse(diff_lines(MULTI_PAR_OUT3, GOOD_MULTI_PAR_OUT3))
            self.assertFalse(diff_lines(MULTI_PAR_OUT4, GOOD_MULTI_PAR_OUT4))
            self.assertFalse(diff_lines(MULTI_PAR_OUT5, GOOD_MULTI_PAR_OUT5))
            self.assertFalse(diff_lines(MULTI_PAR_OUT6, GOOD_MULTI_PAR_OUT6))
        finally:
            for o_file in MULTI_OUT_FILES:
                silent_remove(o_file, disable=DISABLE_REMOVE)

    def testMakeEqPar(self):
        try:
            for o_file in MULTI_OUT_FILES:
                silent_remove(o_file)
            main(["-c", PAR_EQ_INI])
            self.assertFalse(diff_lines(MULTI_PAR_OUT1, GOOD_MULTI_PAR_OUT1))
            self.assertFalse(diff_lines(MULTI_PAR_OUT2, GOOD_PAR_OUT))
            self.assertFalse(diff_lines(MULTI_PAR_OUT3, GOOD_MULTI_PAR_OUT3))
        finally:
            for o_file in MULTI_OUT_FILES:
                silent_remove(o_file, disable=DISABLE_REMOVE)

    def testMakeGPUJob(self):
        try:
            silent_remove(PROD_GPU_JOB_OUT)
            main(["-c", PROD_GPU_JOB_INI])
            self.assertFalse(diff_lines(PROD_GPU_JOB_OUT, GOOD_PROD_GPU_JOB_OUT))
        finally:
            silent_remove(PROD_GPU_JOB_OUT, disable=DISABLE_REMOVE)

    def testMakeGPUInp(self):
        try:
            silent_remove(PROD_GPU_INP_OUT)
            main(["-c", PROD_GPU_INP_INI])
            self.assertFalse(diff_lines(PROD_GPU_INP_OUT, GOOD_PROD_GPU_INP_OUT))
        finally:
            silent_remove(PROD_GPU_INP_OUT, disable=DISABLE_REMOVE)

    def testMakeGPUInpJob(self):
        # Test processing two tpl files with one input; bit redundant with above, but not worried about it
        try:
            silent_remove(PROD_GPU_JOB_OUT)
            silent_remove(PROD_GPU_INP_OUT)
            main(["-c", PROD_GPU_JOB_INP_INI])
            self.assertFalse(diff_lines(PROD_GPU_JOB_OUT, GOOD_PROD_GPU_JOB_OUT))
            self.assertFalse(diff_lines(PROD_GPU_INP_OUT, GOOD_PROD_GPU_INP_OUT))
        finally:
            silent_remove(PROD_GPU_JOB_OUT, disable=DISABLE_REMOVE)
            silent_remove(PROD_GPU_INP_OUT, disable=DISABLE_REMOVE)

    def testMakeCPUINPJOB(self):
        try:
            silent_remove(PROD_CPU_JOB_OUT)
            silent_remove(PROD_CPU_INP_OUT)
            main(["-c", PROD_CPU_JOB_INP_INI])
            self.assertFalse(diff_lines(PROD_CPU_JOB_OUT, GOOD_PROD_CPU_JOB_OUT))
            self.assertFalse(diff_lines(PROD_CPU_INP_OUT, GOOD_PROD_CPU_INP_OUT))
        finally:
            silent_remove(PROD_CPU_JOB_OUT, disable=DISABLE_REMOVE)
            silent_remove(PROD_CPU_INP_OUT, disable=DISABLE_REMOVE)

    def testMakeAMDINPJOB(self):
        try:
            silent_remove(AMD_GPU_JOB_OUT)
            silent_remove(AMD_GPU_INP_OUT)
            main(["-c", AMD_GPU_JOB_INP_INI])
            self.assertFalse(diff_lines(AMD_GPU_JOB_OUT, GOOD_AMD_GPU_JOB_OUT))
            self.assertFalse(diff_lines(AMD_GPU_INP_OUT, GOOD_AMD_GPU_INP_OUT))
        finally:
            silent_remove(AMD_GPU_JOB_OUT, disable=DISABLE_REMOVE)
            silent_remove(AMD_GPU_INP_OUT, disable=DISABLE_REMOVE)
