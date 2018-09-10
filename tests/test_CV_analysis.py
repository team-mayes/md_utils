# coding=utf-8

"""
Tests for md_utils script
"""

import logging
import unittest
import os

from md_utils.CV_analysis import main
from md_utils.md_common import diff_lines, capture_stderr, capture_stdout, silent_remove

__author__ = 'xadams'

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# File Locations #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
CV_ANALYSIS_DIR = os.path.join(DATA_DIR, 'CV_analysis')

LOG_PATH = os.path.join(NAMD_LOG_DIR, 'namd_short.log')
LOG_OUT_DIHEDRAL = os.path.join(NAMD_LOG_DIR, 'namd_short_dihedral.csv')
LOG_OUT_PERFORMANCE = os.path.join(NAMD_LOG_DIR, 'namd_short_performance.csv')
LOG_OUT_TOTAL = os.path.join(NAMD_LOG_DIR, 'namd_short_total.csv')
LOG_OUT_ENERGY = os.path.join(NAMD_LOG_DIR, 'namd_short_energy.csv')
LOG_OUT_STEP = os.path.join(NAMD_LOG_DIR, 'namd_short_total.csv')
LOG_OUT_AMD = os.path.join(NAMD_LOG_DIR, 'namd_short_amdboost.csv')
STATS_OUT = os.path.join(NAMD_LOG_DIR, 'stats_namd_short_dihedral.csv')
GOOD_LOG_OUT_DIHEDRAL = os.path.join(NAMD_LOG_DIR, 'ts_dihedral_good.csv')
GOOD_LOG_OUT_PERFORMANCE = os.path.join(NAMD_LOG_DIR, 'ts_performance_good.csv')
GOOD_LOG_OUT_TOTAL = os.path.join(NAMD_LOG_DIR, 'ts_total_good.csv')
GOOD_LOG_OUT_ENERGY = os.path.join(NAMD_LOG_DIR, 'ts_energy_good.csv')
GOOD_LOG_OUT_STEP = os.path.join(NAMD_LOG_DIR, 'ts_step_good.csv')
GOOD_LOG_OUT_AMD = os.path.join(NAMD_LOG_DIR, 'ts_amd_good.csv')
GOOD_STATS = os.path.join(NAMD_LOG_DIR, 'stats_ts_dihedral_good.csv')

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
        test_input = ["-l", GHOST_LOG_LIST, "-p"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problems reading file:" in output)

    def testNoOptionSelected(self):
        test_input = ["-f", LOG_PATH]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Did not choose to" in output)

    def testBothOptionsSelected(self):
        test_input = ["-f", LOG_PATH, "-d", "-p"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Please select only one" in output)


class TestMain(unittest.TestCase):
    def testDihedralLogFile(self):
        test_input = ["-f", LOG_PATH, "-d"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(LOG_OUT_DIHEDRAL, GOOD_LOG_OUT_DIHEDRAL))
        finally:
            silent_remove(LOG_OUT_DIHEDRAL, disable=DISABLE_REMOVE)

    def testPerformanceLogFile(self):
        test_input = ["-f", LOG_PATH, "-p"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(LOG_OUT_PERFORMANCE, GOOD_LOG_OUT_PERFORMANCE))
        finally:
            silent_remove(LOG_OUT_PERFORMANCE, disable=DISABLE_REMOVE)

    def testTotalLogFile(self):
        test_input = ["-f", LOG_PATH, "-t"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(LOG_OUT_TOTAL, GOOD_LOG_OUT_TOTAL))
        finally:
            silent_remove(LOG_OUT_TOTAL, disable=DISABLE_REMOVE)

    def testBothLogFile(self):
        test_input = ["-f", LOG_PATH, "-d", "-t"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(LOG_OUT_ENERGY, GOOD_LOG_OUT_ENERGY))
        finally:
            silent_remove(LOG_OUT_ENERGY, disable=DISABLE_REMOVE)

    def testStepLogFile(self):

        test_input = ["-f", LOG_PATH, "-t", "-s", "5002000"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(LOG_OUT_STEP, GOOD_LOG_OUT_STEP))
        finally:
            silent_remove(LOG_OUT_STEP, disable=DISABLE_REMOVE)

            # def testLogList(self):
            #     try:
            #         main(["-l", LOG_LIST])
            #         self.assertFalse(diff_lines(LOG_LIST_OUT, GOOD_LOG_LIST_OUT))
            #     finally:
            #         silent_remove(LOG_LIST_OUT)

    def testStats(self):
        test_input = ["-f", LOG_PATH, "-d", "--stats"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(STATS_OUT, GOOD_STATS))
        finally:
            silent_remove(LOG_OUT_DIHEDRAL, disable=DISABLE_REMOVE)
            silent_remove(STATS_OUT, disable=DISABLE_REMOVE)

            # def testLogList(self):
            #     try:
            #         main(["-l", LOG_LIST])
            #         self.assertFalse(diff_lines(LOG_LIST_OUT, GOOD_LOG_LIST_OUT))
            #     finally:
            #         silent_remove(LOG_LIST_OUT)

    def testAMD(self):
        test_input = ["-f", LOG_PATH, "-a"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(LOG_OUT_AMD, GOOD_LOG_OUT_AMD))
        finally:
            silent_remove(LOG_OUT_AMD, disable=DISABLE_REMOVE)
