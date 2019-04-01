# coding=utf-8

"""
"""

import unittest
import logging
import os
from md_utils.md_common import silent_remove, capture_stderr, capture_stdout
from md_utils.plot_PCA import main

__author__ = 'adams'

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
PCA_DIR = os.path.join(DATA_DIR, 'plot_PCA')
COM_FILE = os.path.join(PCA_DIR, 'sugar_protein_indices.txt')
PROD_CSV = os.path.join(PCA_DIR, 'production.csv')
AMD_CSV = os.path.join(PCA_DIR, 'aMD10.csv')
ORIENTATION_LOG = os.path.join(PCA_DIR, 'orientation.log')
QUAT_FILE_DEF_NAME = os.path.join(PCA_DIR, 'orientation_quat.png')
NAME = 'test'
# These PNG names are currently degenerate but weren't always and may not be someday
PNG_2D_FILE = os.path.join(PCA_DIR, 'test.png')
PNG_1D_FILE = os.path.join(PCA_DIR, 'test.png')
PNG_QUAT_FILE = os.path.join(PCA_DIR, 'test_quat.png')
PCA_DIST_OUT = os.path.join(PCA_DIR, 'test_2D.csv')
COM_DIST_OUT = os.path.join(PCA_DIR, 'test_com.csv')
DIST_FILE = os.path.join(PCA_DIR, 'gating.log')
GOOD_DIST_FILE = os.path.join(PCA_DIR, 'dist_good.csv')
GOOD_COMBINED_FILE = os.path.join(PCA_DIR, 'dist_combined_good.csv')
GOOD_STRIDE_FILE = os.path.join(PCA_DIR, 'dist_stride_good.csv')
GOOD_COM_FILE = os.path.join(PCA_DIR, 'com_good.csv')
BAD_NAME = 'test.csv'


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

    def testReadCOM(self):
        test_input = [PROD_CSV, "-n", NAME, "--outdir", PCA_DIR, "-c"]
        try:
            silent_remove(PNG_1D_FILE)
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_1D_FILE))
        finally:
            silent_remove(PNG_1D_FILE, disable=DISABLE_REMOVE)

    def testMultipleFiles(self):
        test_input = ["-n", NAME, "--outdir", PCA_DIR, "-c", PROD_CSV, AMD_CSV]
        try:
            silent_remove(PNG_1D_FILE)
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_1D_FILE))
        finally:
            silent_remove(PNG_1D_FILE, disable=DISABLE_REMOVE)

    def testOrientationPlot(self):
        test_input = ["-o", "-n", NAME, "--outdir", PCA_DIR, ORIENTATION_LOG]
        try:
            silent_remove(PNG_QUAT_FILE)
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_QUAT_FILE))
        finally:
            silent_remove(PNG_QUAT_FILE, disable=DISABLE_REMOVE)

    def testNoName(self):
        test_input = ["-o", "--outdir", PCA_DIR, ORIENTATION_LOG]
        try:
            silent_remove(QUAT_FILE_DEF_NAME)
            main(test_input)
            self.assertTrue(os.path.isfile(QUAT_FILE_DEF_NAME))
        finally:
            silent_remove(QUAT_FILE_DEF_NAME, disable=DISABLE_REMOVE)
