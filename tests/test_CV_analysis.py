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
LIST_PATH = os.path.join(CV_ANALYSIS_DIR, 'list.txt')
QUAT_OUT = os.path.join(CV_ANALYSIS_DIR, 'CV_analysis_quat.log')
DUPLICATE_BASE = os.path.join(CV_ANALYSIS_DIR, 'duplicate')
DUPLICATE_OUT = os.path.join(CV_ANALYSIS_DIR, 'duplicate_quat.log')
DOUBLE_OUT = os.path.join(CV_ANALYSIS_DIR, 'CV_analysis_double.log')
TRAJ_OUT = os.path.join(CV_ANALYSIS_DIR, 'CV_analysis_quat.log')
GATING_OUT = os.path.join(CV_ANALYSIS_DIR, 'CV_analysis_gating.log')
CART_OUT = os.path.join(CV_ANALYSIS_DIR, 'CV_analysis_cartesian.log')
TCL_OUT = os.path.join(CV_ANALYSIS_DIR, 'CV_analysis.tcl')
CV_FILE_OUT = os.path.join(CV_ANALYSIS_DIR, 'orientation_quat.in')

GOOD_QUAT_LOG_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_CV_analysis_quat.log')
GOOD_DOUBLE_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_CV_analysis_double.log')
GOOD_TRAJ_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_CV_analysis_traj.log')
GOOD_GATING_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_CV_analysis_gating.log')
GOOD_CART_OUT = os.path.join(CV_ANALYSIS_DIR, 'good_CV_analysis_cartesian.log')

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

    def testNoFilesInList(self):
        test_input = [TOP_PATH, "-l", EMPTY_LOG_LIST, "-q"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("No trajectory files" in output)

    def testNoSuchFileInList(self):
        test_input = [TOP_PATH, "-l", GHOST_LOG_LIST, "-q"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problems reading file:" in output)

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

    def testAll(self):
        # todo: fix test
        test_input = [TOP_PATH, COOR_PATH, "-q", "-d", "-g", "--cartesian", "--conf", 'in', "-o", CV_ANALYSIS_DIR]
        try:
            main(test_input)
            self.assertFalse(diff_lines(QUAT_OUT, GOOD_QUAT_LOG_OUT))
            self.assertFalse(diff_lines(DOUBLE_OUT, GOOD_DOUBLE_OUT))
            self.assertFalse(diff_lines(GATING_OUT, GOOD_GATING_OUT))
            self.assertFalse(diff_lines(CART_OUT, GOOD_CART_OUT))
        finally:
            silent_remove(QUAT_OUT, disable=DISABLE_REMOVE)
            silent_remove(DOUBLE_OUT, disable=DISABLE_REMOVE)
            silent_remove(GATING_OUT, disable=DISABLE_REMOVE)
            silent_remove(CART_OUT, disable=DISABLE_REMOVE)

    def testMultipleTrajectories(self):
        test_input = [TOP_PATH, COOR_PATH, COOR_PATH, "-q", "-c", "in", "-o", CV_ANALYSIS_DIR]
        try:
            main(test_input)
            self.assertTrue(os.path.isfile(TCL_OUT))
            self.assertTrue(os.path.isfile(CV_FILE_OUT))
        finally:
            silent_remove(TCL_OUT, disable=DISABLE_REMOVE)
            silent_remove(CV_FILE_OUT, disable=DISABLE_REMOVE)

    def testList(self):
        test_input = [TOP_PATH, "-l", LIST_PATH, "-q", "-c", "in", "-o", CV_ANALYSIS_DIR]
        try:
            main(test_input)
            self.assertTrue(os.path.isfile(TCL_OUT))
            self.assertTrue(os.path.isfile(CV_FILE_OUT))
        finally:
            silent_remove(TCL_OUT, disable=DISABLE_REMOVE)
            silent_remove(CV_FILE_OUT, disable=DISABLE_REMOVE)
