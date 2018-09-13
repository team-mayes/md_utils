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

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# File Locations #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
CV_ANALYSIS_DIR = os.path.join(DATA_DIR, 'CV_analysis')

TOP_PATH = os.path.join(CV_ANALYSIS_DIR, 'protein.psf')
COOR_PATH = os.path.join(CV_ANALYSIS_DIR, 'test.pdb')
QUAT_OUT = os.path.join(CV_ANALYSIS_DIR, 'CV_analysis_quat.log')
DUPLICATE_BASE = os.path.join(CV_ANALYSIS_DIR, 'duplicate')
DUPLICATE_OUT = os.path.join(CV_ANALYSIS_DIR, 'duplicate_quat.log')
QUAT_TPL_OUT = os.path.join(CV_ANALYSIS_DIR, 'orientation_quat.in')
FULL_TPL_OUT = os.path.join(CV_ANALYSIS_DIR, 'orientation_full.in')
DOUBLE_TPL_OUT = os.path.join(CV_ANALYSIS_DIR, 'orientation_full_double.in')
FULL_OUT = os.path.join(CV_ANALYSIS_DIR, 'CV_analysis_full.log')
DOUBLE_OUT = os.path.join(CV_ANALYSIS_DIR, 'CV_analysis_full_double.log')
TRAJ_OUT = os.path.join(CV_ANALYSIS_DIR, 'CV_analysis_quat.log')

GOOD_QUAT_TPL_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_orientation_quat.in')
GOOD_FULL_TPL_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_orientation_full.in')
GOOD_DOUBLE_TPL_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_orientation_double.in')
GOOD_QUAT_LOG_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_CV_analysis_quat.log')
GOOD_FULL_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_CV_analysis_full.log')
GOOD_DOUBLE_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_CV_analysis_full_double.log')
GOOD_TRAJ_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_CV_analysis_traj.log')

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

    def testNoTopology(self):
        test_input = [COOR_PATH, "-q"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("No topology file" in output)

    def testNoConformation(self):
        test_input = [TOP_PATH, COOR_PATH, "-q"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Conformation was not" in output)

    def testNoOverwrite(self):
        test_input = [TOP_PATH, COOR_PATH, "-q", "-n", DUPLICATE_BASE]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("exists. Please rename" in output)


class TestMain(unittest.TestCase):
    def testOutQuat(self):
        test_input = [TOP_PATH, COOR_PATH, "-q", "--conf", 'in', "-o", CV_ANALYSIS_DIR]
        try:
            main(test_input)
            self.assertFalse(diff_lines(QUAT_OUT, GOOD_QUAT_LOG_OUT))
        finally:
            silent_remove(QUAT_OUT, disable=DISABLE_REMOVE)

    def testQuatFullDouble(self):
        test_input = [TOP_PATH, COOR_PATH, "-q", "-f", "-d", "--conf", 'in', "-o", CV_ANALYSIS_DIR]
        try:
            main(test_input)
            self.assertFalse(diff_lines(QUAT_OUT, GOOD_QUAT_LOG_OUT))
            self.assertFalse(diff_lines(FULL_OUT, GOOD_FULL_OUT))
            self.assertFalse(diff_lines(DOUBLE_OUT, GOOD_DOUBLE_OUT))
        finally:
            silent_remove(QUAT_OUT, disable=DISABLE_REMOVE)
            silent_remove(FULL_OUT, disable=DISABLE_REMOVE)
            silent_remove(DOUBLE_OUT, disable=DISABLE_REMOVE)

    def testMultipleTraj(self):
        test_input = [TOP_PATH, COOR_PATH, COOR_PATH, "-q", "-c", "in", "-o", CV_ANALYSIS_DIR]
        try:
            main(test_input)
            self.assertFalse(diff_lines(TRAJ_OUT, GOOD_TRAJ_OUT))
        finally:
            silent_remove(TRAJ_OUT, disable=DISABLE_REMOVE)
