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

TOP_PATH = os.path.join(CV_ANALYSIS_DIR, 'protein.psf')
COOR_PATH = os.path.join(CV_ANALYSIS_DIR, '7.7.coor')
QUAT_OUT = os.path.join(CV_ANALYSIS_DIR, 'out_quat.log')
DUPLICATE_BASE = os.path.join(CV_ANALYSIS_DIR, 'duplicate')
DUPLICATE_OUT = os.path.join(CV_ANALYSIS_DIR, 'duplicate_quat.log')

LOG_LIST = os.path.join(CV_ANALYSIS_DIR, 'log_list.txt')
LOG_LIST_OUT = os.path.join(CV_ANALYSIS_DIR, 'log_list_sum.csv')
GOOD_LOG_LIST_OUT = os.path.join(CV_ANALYSIS_DIR, 'log_list_sum_good.csv')

EMPTY_LOG_LIST = os.path.join(CV_ANALYSIS_DIR, 'empty_log_list.txt')
GHOST_LOG_LIST = os.path.join(CV_ANALYSIS_DIR, 'ghost_log_list.txt')


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
        test_input = ["ghost"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not find specified file" in output)

    def testNoSpecifiedFile(self):
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("required: files" in output)

    # def testNoFilesInList(self):
    #     test_input = ["-f", EMPTY_LOG_LIST]
    #     if logger.isEnabledFor(logging.DEBUG):
    #         main(test_input)
    #     with capture_stderr(main, test_input) as output:
    #         self.assertTrue("Found no lammps log data to process from" in output)

    # def testNoSuchFileInList(self):
    #     test_input = ["-l", GHOST_LOG_LIST, "-p"]
    #     if logger.isEnabledFor(logging.DEBUG):
    #         main(test_input)
    #     with capture_stderr(main, test_input) as output:
    #         self.assertTrue("Problems reading file:" in output)

    def testNoOptionSelected(self):
        test_input = [TOP_PATH, COOR_PATH]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Did not choose to" in output)

    def testNoTrajectory(self):
        test_input = [TOP_PATH]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("No trajectory files provided." in output)

    def testNoOverwrite(self):
        test_input = [TOP_PATH, COOR_PATH, "-q", "-n", DUPLICATE_BASE]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("exists. Please rename" in output)


class TestMain(unittest.TestCase):
    def testOutQuat(self):
        test_input = [TOP_PATH, COOR_PATH, "-q", "--conformation", 'out']
        try:
            main(test_input)
            self.assertFalse(diff_lines(QUAT_OUT, GOOD_QUAT_OUT))
        finally:
            silent_remove(QUAT_OUT, disable=DISABLE_REMOVE)

    def testNoOverwrite(self):
        test_input = [TOP_PATH, COOR_PATH, "-q", "--conformation", 'out', "-n", DUPLICATE_OUT]
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
