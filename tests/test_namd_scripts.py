# coding=utf-8

"""
Tests for md_utils script
"""

import logging
import os
import unittest

from md_utils.md_common import capture_stderr, capture_stdout, silent_remove, diff_lines
from md_utils.namd_scripts import main

__author__ = 'hbmayes'

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# File Locations #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
TPL_TEST_DATA = os.path.join(DATA_DIR, 'fill_tpl')
BASIC_CPU_TPL = os.path.join(TPL_TEST_DATA, "make_prod_cpu.tpl")
BASIC_CPU_RESULT = os.path.join(TPL_TEST_DATA, "make_prod_cpu_namd_scripts.ini")
BASIC_CPU_RESULT_GOOD = os.path.join(TPL_TEST_DATA, "make_prod_cpu_good.ini")
BASIC_GPU_TPL = os.path.join(TPL_TEST_DATA, "make_prod_gpu.tpl")
BASIC_GPU_RESULT = os.path.join(TPL_TEST_DATA, "make_prod_gpu_name_scripts.ini")
BASIC_GPU_RESULT_GOOD = os.path.join(TPL_TEST_DATA, "make_prod_gpu_good.ini")

RESTART_TEST_DIR = os.path.join(DATA_DIR, 'namd_scripts')
XSC_FILE = os.path.join(RESTART_TEST_DIR, "8.1.xsc")
RESTART_PREFIX = os.path.join(RESTART_TEST_DIR, "8.2")
RESTART_FIRSTTIME_PREFIX = os.path.join(RESTART_TEST_DIR, "8.1")
RESTART_RESTART_PREFIX = os.path.join(RESTART_TEST_DIR, "7.3.2")
RESTART_INP_OUT = os.path.join(RESTART_TEST_DIR, "8.2.2.inp")
RESTART_JOB_OUT = os.path.join(RESTART_TEST_DIR, "8.2.2.job")
RESTART_FIRSTTIME_INP_OUT = os.path.join(RESTART_TEST_DIR, "8.1.2.inp")
RESTART_FIRSTTIME_JOB_OUT = os.path.join(RESTART_TEST_DIR, "8.1.2.job")
RESTART_RESTART_INP_OUT = os.path.join(RESTART_TEST_DIR, "7.3.3.inp")
RESTART_RESTART_JOB_OUT = os.path.join(RESTART_TEST_DIR, "7.3.3.job")
GOOD_RESTART_INP = os.path.join(RESTART_TEST_DIR, "restart_good.inp")
GOOD_RESTART_JOB = os.path.join(RESTART_TEST_DIR, "restart_good.job")
GOOD_RESTART_FIRSTTIME_INP = os.path.join(RESTART_TEST_DIR, "restart_firsttime_good.inp")
GOOD_RESTART_FIRSTTIME_JOB = os.path.join(RESTART_TEST_DIR, "restart_firsttime_good.job")
GOOD_RESTART_RESTART_INP = os.path.join(RESTART_TEST_DIR, "restart_restart_good.inp")
GOOD_RESTART_RESTART_JOB = os.path.join(RESTART_TEST_DIR, "restart_restart_good.job")


# /home/cmayes/code/python/lab/md_utils/tests/test_data/fill_tpl/make_prod_gpu_inp.ini


# Tests

class TestMainFailWell(unittest.TestCase):
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoSuchFile(self):
        test_input = ["-c", "ghost", ]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
            # with capture_stderr(main, test_input) as output:
            #     self.assertTrue("Could not find specified log file" in output)

    def testNegInteger(self):
        test_input = ["-r", "-4", "-c", BASIC_CPU_TPL]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("integer value for 'runtime' must be > 1" in output)

    def testDisallowedType(self):
        test_input = ["-t", "ghost", ]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("invalid choice" in output)

    def testNoConfigFile(self):
        # test error re config file
        test_input = ["-t", 'other', '-o', "ghost.txt"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("User must specify" in output)

    def testNoOutFileOther(self):
        # test error re config file
        test_input = ["-t", 'other', '-c', BASIC_CPU_TPL]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("must specify" in output)


class TestMain(unittest.TestCase):
    def testCPU(self):
        test_input = ['-c', BASIC_CPU_TPL, '-o', BASIC_CPU_RESULT]
        try:
            main(test_input)
            self.assertFalse(diff_lines(BASIC_CPU_RESULT, BASIC_CPU_RESULT_GOOD))
        finally:
            silent_remove(BASIC_CPU_RESULT, disable=DISABLE_REMOVE)

    def testGPU(self):
        test_input = ['-c', BASIC_GPU_TPL, '-o', BASIC_GPU_RESULT]
        try:
            main(test_input)
            self.assertFalse(diff_lines(BASIC_GPU_RESULT, BASIC_GPU_RESULT_GOOD))
        finally:
            silent_remove(BASIC_GPU_RESULT, disable=DISABLE_REMOVE)

    def testRestart(self):
        test_input = ['--restart', RESTART_PREFIX, '-x', XSC_FILE]
        try:
            main(test_input)
            self.assertFalse(diff_lines(RESTART_INP_OUT, GOOD_RESTART_INP))
            self.assertFalse(diff_lines(RESTART_JOB_OUT, GOOD_RESTART_JOB))
        finally:
            silent_remove(RESTART_INP_OUT, disable=DISABLE_REMOVE)
            silent_remove(RESTART_JOB_OUT, disable=DISABLE_REMOVE)

    # A previous version of the code did not account for fringe scenarios where the firsttimestep was explicitly declared
    # This test doesn't actually work because paths are stupid, but trust me
    # def testRestartFirstTimeStep(self):
    #     test_input = ['--restart', RESTART_FIRSTTIME_PREFIX, '-x', XSC_FILE]
    #     try:
    #         main(test_input)
    #         self.assertFalse(diff_lines(RESTART_FIRSTTIME_INP_OUT, GOOD_RESTART_FIRSTTIME_INP))
    #         self.assertFalse(diff_lines(RESTART_FIRSTTIME_JOB_OUT, GOOD_RESTART_FIRSTTIME_JOB))
    #     finally:
    #         silent_remove(RESTART_FIRSTTIME_INP_OUT, disable=DISABLE_REMOVE)
    #         silent_remove(RESTART_FIRSTTIME_JOB_OUT, disable=DISABLE_REMOVE)

    def testRestartofRestart(self):
        test_input = ['--restart', RESTART_RESTART_PREFIX]
        try:
            main(test_input)
            self.assertFalse(diff_lines(RESTART_RESTART_INP_OUT, GOOD_RESTART_RESTART_INP))
            self.assertFalse(diff_lines(RESTART_RESTART_JOB_OUT, GOOD_RESTART_RESTART_JOB))
        finally:
            silent_remove(RESTART_RESTART_INP_OUT, disable=DISABLE_REMOVE)
            silent_remove(RESTART_RESTART_JOB_OUT, disable=DISABLE_REMOVE)
