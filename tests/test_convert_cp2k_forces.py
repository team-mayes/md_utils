# coding=utf-8

"""
Tests for convert_cp2k_forces.py.
"""
import logging
import os
import unittest
from md_utils.convert_cp2k_forces import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
CP2K_DATA_DIR = os.path.join(DATA_DIR, 'cp2k_files')

# Input and output files for testing elegant failure #

INCOMP_F_LIST = os.path.join(CP2K_DATA_DIR, 'cp2k_force_list_incomp.txt')
# noinspection PyUnresolvedReferences
BAD_F_LIST = os.path.join(CP2K_DATA_DIR, 'cp2k_force_list_bad.txt')
NOT_GLU_ATOM_NUM = '142'
GHOST_STRING = 'ghost'

# Input and output files for validating output #

GLU_FILE = os.path.join(CP2K_DATA_DIR, '0.750_20c_100ps_reorder_555260.dat')
GLU_ATOM_NUM = '1429'
GLU_LIST = os.path.join(CP2K_DATA_DIR, 'cp2k_glu_force_list.txt')
GLU_SUM = os.path.join(CP2K_DATA_DIR, 'force_sums_cp2k_glu_force_list.csv')
GOOD_GLU_SUM = os.path.join(CP2K_DATA_DIR, 'force_sums_cp2k_glu_force_list_good.csv')
# noinspection PyUnresolvedReferences
GLU_OUT1 = os.path.join(CP2K_DATA_DIR, 'REF_0.750_20c_100ps_reorder_555260')
GOOD_GLU_OUT1 = os.path.join(CP2K_DATA_DIR, 'REF_0.750_20c_100ps_reorder_555260_good')
# noinspection PyUnresolvedReferences
GLU_OUT2 = os.path.join(CP2K_DATA_DIR, 'REF_1.000_20c_100ps_reorder_485050')
GOOD_GLU_OUT2 = os.path.join(CP2K_DATA_DIR, 'REF_1.000_20c_100ps_reorder_485050_good')

GLU_FILE_2QM = os.path.join(CP2K_DATA_DIR, '1.250_20c_100ps_reorder_526120.dat')
GLU_2QM_OUT = os.path.join(CP2K_DATA_DIR, 'REF_1.250_20c_100ps_reorder_526120')
GOOD_GLU_2QM_OUT = os.path.join(CP2K_DATA_DIR, 'REF_1.250_20c_100ps_reorder_526120_good')

GLU_FILE_MM_AFTER_QM = os.path.join(CP2K_DATA_DIR, '1.250_20c_526120_mm_after_qm.dat')
GLU_2MM_AFTER_QM_OUT = os.path.join(CP2K_DATA_DIR, 'REF_1.250_20c_526120_mm_after_qm')


class TestConvertCP2KFailWell(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(main, []) as output:
            self.assertTrue("show this help message" in output)
        with capture_stderr(main, []) as output:
            self.assertTrue("WARNING:  Default file" in output)

    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testUnregArg(self):
        test_input = ['-@@@', "-l", GLU_LIST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("unrecognized arguments" in output)

    def testNonIntAtomNum(self):
        test_input = ["-n", "ghost", "-l", GLU_LIST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not convert specified num_atoms ('ghost') to an integer." in output)

    def testMissingFile(self):
        test_input = ["-f", GHOST_STRING]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Missing specified file" in output)

    def testMissingFileList(self):
        test_input = ["-l", " "]
        with capture_stdout(main, test_input) as output:
            self.assertTrue("show this help message" in output)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Specified file listing cp2k force files missing" in output)

    def testMissingIncompleteFile(self):
        test_input = ["-l", INCOMP_F_LIST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stderr(main, test_input) as output:
                self.assertTrue("Check file" in output)
                self.assertTrue("Could not read file" in output)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("1429     -0.215      0.156     -0.387      0.470" in output)
            self.assertFalse(diff_lines(GLU_OUT1, GOOD_GLU_OUT1))
        finally:
            silent_remove(GLU_OUT1)

    def testBadDir(self):
        with capture_stderr(main, ["-d", 'ghost', "-l", GLU_LIST]) as output:
            self.assertTrue("Cannot find specified output directory" in output)

    def testNoSuchOption(self):
        with capture_stderr(main, ["-@", GLU_LIST]) as output:
            self.assertTrue("unrecognized argument" in output)
            self.assertTrue(GLU_LIST in output)

    def testBadForceFile(self):
        test_input = ["-l", BAD_F_LIST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("WARNING:  Did not find the expected four force values" in output)
            self.assertTrue("Check file: " in output)
            self.assertTrue("end of file without encountering the expected QMMM" in output)
            self.assertTrue("read 2 summary force sections" in output)
            self.assertTrue("WARNING:  Did not find six expected values" in output)
            self.assertTrue("WARNING:  No valid cp2k force output files were read" in output)

    def testWrongGluNumAtoms(self):
        test_input = ["-f", GLU_FILE, "-n", NOT_GLU_ATOM_NUM]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue(NOT_GLU_ATOM_NUM in output)
            self.assertTrue(GLU_ATOM_NUM in output)


class TestConvertCP2K(unittest.TestCase):
    def testGoodAtomNumFile(self):
        test_input = ["-f", GLU_FILE, "-n", GLU_ATOM_NUM]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue("1429     -0.215      0.156     -0.387      0.470" in output)
            self.assertFalse(diff_lines(GLU_OUT1, GOOD_GLU_OUT1))
        finally:
            silent_remove(GLU_OUT1, disable=DISABLE_REMOVE)

    def testGoodInput(self):
        test_input = ["-l", GLU_LIST]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue("1429     -0.274     -0.728     -0.387      0.470" in output)
                self.assertTrue("1429     -0.215      0.156      0.269      0.822" in output)
            self.assertFalse(diff_lines(GLU_SUM, GLU_SUM))
            self.assertFalse(diff_lines(GLU_OUT1, GOOD_GLU_OUT1))
            self.assertFalse(diff_lines(GLU_OUT2, GOOD_GLU_OUT2))
        finally:
            silent_remove(GLU_SUM, disable=DISABLE_REMOVE)
            silent_remove(GLU_OUT1, disable=DISABLE_REMOVE)
            silent_remove(GLU_OUT2, disable=DISABLE_REMOVE)

    def testQMTwice(self):
        test_input = ["-f", GLU_FILE_2QM, "-n", GLU_ATOM_NUM]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue("1429      0.065     -0.677     -0.401      0.789" in output)
                self.assertTrue("Found 44 QM atoms" in output)
            self.assertFalse(diff_lines(GLU_2QM_OUT, GOOD_GLU_2QM_OUT))
        finally:
            silent_remove(GLU_2QM_OUT, disable=DISABLE_REMOVE)

    def testMMAfterQM(self):
        test_input = ["-f", GLU_FILE_MM_AFTER_QM, "-n", GLU_ATOM_NUM]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue("1429      0.065     -0.677     -0.401      0.789" in output)
            self.assertFalse(diff_lines(GLU_2MM_AFTER_QM_OUT, GOOD_GLU_2QM_OUT))
        finally:
            silent_remove(GLU_2MM_AFTER_QM_OUT, disable=DISABLE_REMOVE)
