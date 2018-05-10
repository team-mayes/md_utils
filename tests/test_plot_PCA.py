# coding=utf-8

"""
"""

import unittest
import logging
import os
from md_utils.md_common import silent_remove, capture_stderr, capture_stdout, diff_lines
from md_utils.plot_PCA import main

__author__ = 'adams'

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
PCA_DIR = os.path.join(DATA_DIR, 'plot_PCA')
TRAJ_FILE = os.path.join(PCA_DIR, 'short.dcd')
TOP_FILE = os.path.join(PCA_DIR, 'step5_assembly.xplor_ext.psf')
IG_FILE = os.path.join(PCA_DIR, 'IG_indices.txt')
EG_FILE = os.path.join(PCA_DIR, 'EG_indices.txt')
COM_FILE = os.path.join(PCA_DIR, 'sugar_protein_indices.txt')
PROD_CSV = os.path.join(PCA_DIR, 'production.csv')
AMD_CSV = os.path.join(PCA_DIR, 'aMD10.csv')
ORIENTATION_LOG = os.path.join(PCA_DIR, 'orientation.log')
QUAT_FILE_DEF_NAME = os.path.join(PCA_DIR, 'orientation_quat.png')
NAME = 'test'
CFG_FILE = os.path.join(PCA_DIR, 'plot_pca.ini')
# These PNG names are currently degenerate but weren't always and may not be someday
PNG_2D_FILE = os.path.join(PCA_DIR, 'test.png')
PNG_1D_FILE = os.path.join(PCA_DIR, 'test.png')
PNG_QUAT_FILE = os.path.join(PCA_DIR, 'test_quat.png')
TRAJ_GLOB = os.path.join(PCA_DIR, '*dcd')
PCA_DIST_OUT = os.path.join(PCA_DIR, 'test_2D.csv')
COM_DIST_OUT = os.path.join(PCA_DIR, 'test_com.csv')
GOOD_DIST_FILE = os.path.join(PCA_DIR, 'dist_good.csv')
GOOD_APPEND_FILE = os.path.join(PCA_DIR, 'dist_append_good.csv')
GOOD_COMBINED_FILE = os.path.join(PCA_DIR, 'dist_combined_good.csv')
GOOD_STRIDE_FILE = os.path.join(PCA_DIR, 'dist_stride_good.csv')
GOOD_COM_FILE = os.path.join(PCA_DIR, 'com_good.csv')
BAD_LIST = os.path.join(PCA_DIR, 'bad_list.txt')
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
        test_input = ['-t', 'ghost']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not find" in output)

    def testBadFileInList(self):
        test_input = ['-l', BAD_LIST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not find" in output)

    def testNegativeStride(self):
        test_input = ["--traj", TRAJ_FILE, "--top", TOP_FILE, "-i", EG_FILE, IG_FILE, "-n", NAME, "--outdir", PCA_DIR,
                      "-s", '-2']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("must be > 1" in output)

    def testBothFlags(self):
        test_input = ["-n", NAME, "--outdir", PCA_DIR, "-c", "-f", PROD_CSV, "-o"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Cannot flag both" in output)

    def testOrientationTraj(self):
        test_input = ["--traj", TRAJ_FILE, "--top", TOP_FILE, "-i", EG_FILE, IG_FILE, "-n", NAME, "--outdir", PCA_DIR,
                      "-o"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("not currently configured" in output)

    def testBadName(self):
        test_input = ["-n", BAD_NAME, "--outdir", PCA_DIR, "-f", GOOD_DIST_FILE]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("Removing extension" in output)
        silent_remove(PNG_2D_FILE, disable=DISABLE_REMOVE)

# This catches an error that is no longer relevant
#     def testOrientationWrite(self):
#         test_input = ["-n", NAME, "--outdir", PCA_DIR, "-o", "-w"]
#         if logger.isEnabledFor(logging.DEBUG):
#             main(test_input)
#         with capture_stderr(main, test_input) as output:
#             self.assertTrue("write orientation data" in output)


class TestMain(unittest.TestCase):
    def testWithProtxData(self):
        test_input = ["--traj", TRAJ_FILE, "--top", TOP_FILE, "-i", EG_FILE, IG_FILE, "-n", NAME, "--outdir", PCA_DIR]
        try:
            # silent_remove(PNG_2D_FILE)
            silent_remove(PCA_DIST_OUT)
            main(test_input)
            self.assertFalse(diff_lines(PCA_DIST_OUT, GOOD_DIST_FILE))
            # self.assertTrue(os.path.isfile(PNG_2D_FILE))
        finally:
            silent_remove(PCA_DIST_OUT, disable=DISABLE_REMOVE)
            # silent_remove(PNG_2D_FILE, disable=DISABLE_REMOVE)

    def testWriteDistances(self):
        test_input = ["-t", TRAJ_FILE, "-p", TOP_FILE, "-i", EG_FILE, IG_FILE, "-n", NAME, "--outdir", PCA_DIR]
        try:
            silent_remove(PCA_DIST_OUT)
            main(test_input)
            self.assertFalse(diff_lines(PCA_DIST_OUT, GOOD_DIST_FILE))
        finally:
            silent_remove(PCA_DIST_OUT, disable=DISABLE_REMOVE)

    def testStride(self):
        test_input = ["-t", TRAJ_FILE, "-p", TOP_FILE, "-i", EG_FILE, IG_FILE, "-n", NAME, "--outdir", PCA_DIR,
                      "-s", "2"]
        try:
            silent_remove(PCA_DIST_OUT)
            main(test_input)
            self.assertFalse(diff_lines(PCA_DIST_OUT, GOOD_STRIDE_FILE))
        finally:
            silent_remove(PCA_DIST_OUT, disable=DISABLE_REMOVE)

    def testAppendDistances(self):
        test_input = ["-t", TRAJ_FILE, "-p", TOP_FILE, "-i", EG_FILE, IG_FILE, "-n", NAME, "--outdir", PCA_DIR]
        try:
            silent_remove(PCA_DIST_OUT)
            # The append happens in place, so the base file must first be generated
            main(test_input)
            main(test_input)
            self.assertFalse(diff_lines(PCA_DIST_OUT, GOOD_APPEND_FILE))
        finally:
            silent_remove(PCA_DIST_OUT, disable=DISABLE_REMOVE)

    def testReadDistances(self):
        test_input = ["-n", NAME, "--outdir", PCA_DIR, "-f", GOOD_DIST_FILE]
        try:
            silent_remove(PNG_2D_FILE)
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_2D_FILE))
        finally:
            silent_remove(PNG_2D_FILE, disable=DISABLE_REMOVE)

    def testReadAppend(self):
        test_input = ["-n", NAME, "--outdir", PCA_DIR, "-f", GOOD_APPEND_FILE]
        try:
            silent_remove(PNG_2D_FILE)
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_2D_FILE))
        finally:
            silent_remove(PNG_2D_FILE, disable=DISABLE_REMOVE)

# This test cannot be performed the way the script is now configured to write files
    # def testCombineData(self):
    #     test_input = ["-n", NAME, "--outdir", PCA_DIR, "-f", GOOD_APPEND_FILE]
    #     try:
    #         silent_remove(PCA_DIST_OUT)
    #         main(test_input)
    #         self.assertFalse(diff_lines(PCA_DIST_OUT, GOOD_COMBINED_FILE))
    #     finally:
    #         silent_remove(PCA_DIST_OUT, disable=DISABLE_REMOVE)

    def testCoMPlot(self):
        test_input = ["--traj", TRAJ_FILE, "--top", TOP_FILE, "-i", COM_FILE, "-n", NAME, "--outdir", PCA_DIR, "-c"]
        try:
            silent_remove(COM_DIST_OUT)
            main(test_input)
            self.assertFalse(diff_lines(COM_DIST_OUT, GOOD_COM_FILE))
            # self.assertTrue(os.path.isfile(PNG_1D_FILE))
        finally:
            silent_remove(COM_DIST_OUT, disable=DISABLE_REMOVE)
            # silent_remove(PNG_1D_FILE, disable=DISABLE_REMOVE)

    def testReadCOM(self):
        test_input = ["-n", NAME, "--outdir", PCA_DIR, "-c", "-f", PROD_CSV]
        try:
            silent_remove(PNG_1D_FILE)
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_1D_FILE))
        finally:
            silent_remove(PNG_1D_FILE, disable=DISABLE_REMOVE)

    def testMultipleFiles(self):
        test_input = ["-n", NAME, "--outdir", PCA_DIR, "-c", "-f", PROD_CSV, AMD_CSV]
        try:
            silent_remove(PNG_1D_FILE)
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_1D_FILE))
        finally:
            silent_remove(PNG_1D_FILE, disable=DISABLE_REMOVE)

    def testIniFile(self):
        test_input = ["--config", CFG_FILE, "--traj", TRAJ_FILE, "--outdir", PCA_DIR]
        try:
            silent_remove(PNG_2D_FILE)
            silent_remove(PCA_DIST_OUT)
            main(test_input)
            # self.assertTrue(os.path.isfile(PNG_2D_FILE))
            self.assertFalse(diff_lines(PCA_DIST_OUT, GOOD_DIST_FILE))
        finally:
            silent_remove(PCA_DIST_OUT, disable=DISABLE_REMOVE)
            # silent_remove(PNG_2D_FILE, disable=DISABLE_REMOVE)

    def testOrientationPlot(self):
        test_input = ["-o", "-n", NAME, "--outdir", PCA_DIR, "-f", ORIENTATION_LOG]
        try:
            silent_remove(PNG_QUAT_FILE)
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_QUAT_FILE))
        finally:
            silent_remove(PNG_QUAT_FILE, disable=DISABLE_REMOVE)

    def testNoName(self):
        test_input = ["-o", "--outdir", PCA_DIR, "-f", ORIENTATION_LOG]
        try:
            silent_remove(QUAT_FILE_DEF_NAME)
            main(test_input)
            self.assertTrue(os.path.isfile(QUAT_FILE_DEF_NAME))
        finally:
            silent_remove(QUAT_FILE_DEF_NAME, disable=DISABLE_REMOVE)
