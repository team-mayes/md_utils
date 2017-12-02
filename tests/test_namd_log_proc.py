# coding=utf-8

"""
Tests for md_utils script
"""

import logging
import unittest
import os

from md_utils.namd_log_proc import main
from md_utils.md_common import diff_lines, capture_stderr, capture_stdout, silent_remove

__author__ = 'hbmayes'

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# File Locations #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
NAMD_LOG_DIR = os.path.join(DATA_DIR, 'namd_log_proc')

LOG_PATH = os.path.join(NAMD_LOG_DIR, 'namd_short.log')
LOG_OUT = os.path.join(NAMD_LOG_DIR, 'namd_short_sum.csv')
GOOD_LOG_OUT = os.path.join(NAMD_LOG_DIR, 'ts_energy_good.csv')

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
        test_input = ["-f", "ghost", ]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not find specified log file" in output)

    def testNoSpecifiedFile(self):
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Found no log file names to process" in output)

    # def testNoFilesInList(self):
    #     test_input = ["-f", EMPTY_LOG_LIST]
    #     if logger.isEnabledFor(logging.DEBUG):
    #         main(test_input)
    #     with capture_stderr(main, test_input) as output:
    #         self.assertTrue("Found no lammps log data to process from" in output)

    def testNoSuchFileInList(self):
        test_input = ["-l", GHOST_LOG_LIST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue(" No such file or directory" in output)

    # TODO: add test for error when neither -s nor -t selected


class TestMain(unittest.TestCase):
    def testLogFile(self):
        test_input = ["-f", LOG_PATH, "-t"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(LOG_OUT, GOOD_LOG_OUT))
        finally:
            silent_remove(LOG_OUT, disable=DISABLE_REMOVE)

    # def testLogList(self):
    #     try:
    #         main(["-l", LOG_LIST])
    #         self.assertFalse(diff_lines(LOG_LIST_OUT, GOOD_LOG_LIST_OUT))
    #     finally:
    #         silent_remove(LOG_LIST_OUT)
