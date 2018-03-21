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

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# File Locations #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
TPL_TEST_DATA = os.path.join(DATA_DIR, 'fill_tpl')
BASIC_CPU_TPL = os.path.join(TPL_TEST_DATA, "make_prod_cpu.tpl")
BASIC_CPU_RESULT = os.path.join(TPL_TEST_DATA, "make_prod_cpu_namd_scripts.ini")
BASIC_CPU_RESULT_GOOD = os.path.join(TPL_TEST_DATA, "make_prod_cpu_good.ini")



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

    def testNotInteger(self):
        test_input = ["-f", "four", ]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("invalid int" in output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNegInteger(self):
        test_input = ["-r", "-4", "-c", BASIC_CPU_TPL]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("integer value for 'run' must be > 1" in output)

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
            diff_lines(BASIC_CPU_RESULT, BASIC_CPU_RESULT_GOOD)
        finally:
            silent_remove(BASIC_CPU_RESULT, disable=DISABLE_REMOVE)
