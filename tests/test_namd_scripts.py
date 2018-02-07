# coding=utf-8

"""
Tests for md_utils script
"""

import logging
import unittest
import os

from md_utils.namd_scripts import main
from md_utils.md_common import diff_lines, capture_stderr, capture_stdout, silent_remove

__author__ = 'hbmayes'

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# File Locations #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
NAMD_LOG_DIR = os.path.join(DATA_DIR, 'namd_scripts')

LOG_PATH = os.path.join(NAMD_LOG_DIR, 'namd_short.log')
LOG_OUT_SUMMARY = os.path.join(NAMD_LOG_DIR, 'namd_short_sum.csv')
LOG_OUT_PERFORMANCE = os.path.join(NAMD_LOG_DIR, 'namd_short_performance.csv')
GOOD_LOG_OUT_SUMMARY = os.path.join(NAMD_LOG_DIR, 'ts_energy_good.csv')
GOOD_LOG_OUT_PERFORMANCE = os.path.join(NAMD_LOG_DIR, 'ts_performance_good.csv')
DEF_TPL = os.path.join(NAMD_LOG_DIR, )

LOG_LIST = os.path.join(NAMD_LOG_DIR, 'log_list.txt')
LOG_LIST_OUT = os.path.join(NAMD_LOG_DIR, 'log_list_sum.csv')
GOOD_LOG_LIST_OUT = os.path.join(NAMD_LOG_DIR, 'log_list_sum_good.csv')

EMPTY_LOG_LIST = os.path.join(NAMD_LOG_DIR, 'empty_log_list.txt')
GHOST_LOG_LIST = os.path.join(NAMD_LOG_DIR, 'ghost_log_list.txt')


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
        test_input = ["-r", "-4", ]
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

    def testNoSpecifiedFile(self):
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Found no log file names to process" in output)

    def testNoConfigFile(self):
        # test error re config file
        test_input = ["-t", 'other', '-o', "ghost.txt"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("User must specify" in output)

    def testNoOutFileOther(self):
        # test error re config file
        test_input = ["-t", 'other', '-c', "make_prod_cpu.tpl"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("must be specified" in output)


class TestMain(unittest.TestCase):
    def testCPU(self):
        test_input = [-c DEF_TPL]
        try:
            main(test_input)
            # self.assertFalse(diff_lines(LOG_OUT_SUMMARY, GOOD_LOG_OUT_SUMMARY))
        finally:
            silent_remove(LOG_OUT_SUMMARY, disable=DISABLE_REMOVE)
