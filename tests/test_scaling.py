# coding=utf-8

"""
"""

import unittest
import logging
import os
from md_utils.md_common import silent_remove, capture_stderr, capture_stdout, diff_lines
from md_utils.scaling import main

__author__ = 'xadams'

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
PCA_DIR = os.path.join(DATA_DIR, 'plot_PCA')
COM_FILE = os.path.join(PCA_DIR, 'sugar_protein_indices.txt')


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
        test_input = ['ghost']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not find" in output)

    def testBothFlags(self):
        test_input = [PROD_CSV, "-n", NAME, "--outdir", PCA_DIR, "-c", "-o"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Cannot flag both" in output)

    def testBadName(self):
        test_input = [DIST_FILE, "-n", BAD_NAME, "--outdir", PCA_DIR]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("Removing extension" in output)
        silent_remove(PNG_2D_FILE, disable=DISABLE_REMOVE)


class TestMain(unittest.TestCase):
    def testReadDistances(self):
        test_input = [DIST_FILE, "-n", NAME, "--outdir", PCA_DIR]
        try:
            silent_remove(PNG_2D_FILE)
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_2D_FILE))
        finally:
            silent_remove(PNG_2D_FILE, disable=DISABLE_REMOVE)

