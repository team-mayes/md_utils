import logging
import unittest
import os

from md_utils.cp2k2data import main
from md_utils.md_common import (diff_lines, silent_remove, capture_stderr, capture_stdout)

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'

# Directories #

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'cp2k2data')

# For testing good input/output #

ONE_FILE_INI = os.path.join(SUB_DATA_DIR, 'cp2k2data.ini')
GLU_DATA_OUT = os.path.join(SUB_DATA_DIR, 'glu_3.0_1.075.data')
GOOD_GLU_DATA_OUT = os.path.join(SUB_DATA_DIR, 'glu_3.0_1.075_good.data')

MULT_FILE_INI = os.path.join(SUB_DATA_DIR, 'cp2k2data_mult.ini')
GLU_DATA_OUT2 = os.path.join(SUB_DATA_DIR, 'glu_2.5_1.0.data')
GOOD_GLU_DATA_OUT2 = os.path.join(SUB_DATA_DIR, 'glu_2.5_1.0_good.data')

# For testing catching errors #

MISSING_TEMPLATE_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_miss_file.ini')
CUTOFF_CP2K_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_cutoff.ini')
TOO_FEW_CP2K_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_too_few.ini')
TOO_MANY_CP2K_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_too_many.ini')
NO_FILES_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_no_files.ini')
MISSING_KEY_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_missing_key.ini')


class TestData2DataFailWell(unittest.TestCase):

    def testNoDefault(self):
        test_input = []
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not read file" in output)

    def testMissingTemplateFile(self):
        test_input = ["-c", MISSING_TEMPLATE_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("No such file or directory" in output)

    def testCutoffCP2KOutput(self):
        test_input = ["-c", CUTOFF_CP2K_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Did not read coordinates" in output)

    def testTooFewAtoms(self):
        test_input = ["-c", TOO_FEW_CP2K_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Expected to read coordinates" in output)

    def testTooManyAtoms(self):
        test_input = ["-c", TOO_MANY_CP2K_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("After reading" in output)

    def testNoFiles(self):
        test_input = ["-c", NO_FILES_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Found no file names to process" in output)

    def testMissingKey(self):
        test_input = ["-c", MISSING_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Missing config val" in output)


class TestCP2K2Data(unittest.TestCase):
    def testHelpOption(self):
        test_input = ["-h"]
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)
        with capture_stderr(main, test_input) as output:
            self.assertEqual(len(output), 0)

    def testOneFile(self):
        # When checking output, ignore differences in version and time
        try:
            main(["-c", ONE_FILE_INI])
            diffs = diff_lines(GLU_DATA_OUT, GOOD_GLU_DATA_OUT)
            self.assertEquals(len(diffs), 2)
            self.assertTrue("Created on " in diffs[0])
        finally:
            silent_remove(GLU_DATA_OUT, disable=DISABLE_REMOVE)

    def testFileList(self):
        try:
            silent_remove(GLU_DATA_OUT)
            test_input = ["-c", MULT_FILE_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("tests/test_data/cp2k2data/glu_2.5_1.0.out energy: -283.342271788704181" in output)
                self.assertTrue("tests/test_data/cp2k2data/glu_3.0_1.075.out energy: -472.455097972129295" in output)
            diffs = diff_lines(GLU_DATA_OUT, GOOD_GLU_DATA_OUT)
            diffs1 = diff_lines(GLU_DATA_OUT2, GOOD_GLU_DATA_OUT2)
            for diff_list in [diffs, diffs1]:
                self.assertEquals(len(diff_list), 2)
                self.assertTrue("Created on " in diff_list[0])
        finally:
            silent_remove(GLU_DATA_OUT, disable=DISABLE_REMOVE)
            silent_remove(GLU_DATA_OUT2, disable=DISABLE_REMOVE)
