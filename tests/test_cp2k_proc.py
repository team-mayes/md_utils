import logging
import unittest
import os

from md_utils.cp2k_proc import main
from md_utils.md_common import (diff_lines, silent_remove, capture_stderr, capture_stdout)

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'

# Directories #

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'cp2k_proc')

# For testing good input/output #

ONE_2DATA_INI = os.path.join(SUB_DATA_DIR, 'cp2k2data.ini')
GLU_DATA_OUT = os.path.join(SUB_DATA_DIR, 'glu_3.0_1.075.data')
GOOD_GLU_DATA_OUT = os.path.join(SUB_DATA_DIR, 'glu_3.0_1.075_good.data')
GLU_XYZ_OUT = os.path.join(SUB_DATA_DIR, 'glu_3.0_1.075.xyz')
GOOD_GLU_XYZ_OUT = os.path.join(SUB_DATA_DIR, 'glu_3.0_1.075_good.xyz')

MULT_2PDB_INI = os.path.join(SUB_DATA_DIR, 'cp2k2pdb.ini')
GLU_PDB_OUT = os.path.join(SUB_DATA_DIR, 'glu_3.0_1.075.pdb')
GOOD_GLU_PDB_OUT = os.path.join(SUB_DATA_DIR, 'glu_3.0_1.075_good.pdb')
GLU_PDB_OUT1 = os.path.join(SUB_DATA_DIR, 'glu_2.5_1.05-1.pdb')
GLU_PDB_OUT2 = os.path.join(SUB_DATA_DIR, 'glu_2.5_1.0.pdb')
GOOD_GLU_PDB_OUT2 = os.path.join(SUB_DATA_DIR, 'glu_2.5_1.0_good.pdb')
GLU_XYZ_OUT1 = os.path.join(SUB_DATA_DIR, 'glu_2.5_1.05-1.xyz')
GLU_XYZ_OUT2 = os.path.join(SUB_DATA_DIR, 'glu_2.5_1.0.xyz')

MULT_2DATA_INI = os.path.join(SUB_DATA_DIR, 'cp2k2data_mult.ini')
GLU_DATA_OUT1 = os.path.join(SUB_DATA_DIR, 'glu_2.5_1.05-1.data')
GLU_DATA_OUT2 = os.path.join(SUB_DATA_DIR, 'glu_2.5_1.0.data')
GOOD_GLU_DATA_OUT2 = os.path.join(SUB_DATA_DIR, 'glu_2.5_1.0_good.data')

XYZ_ONLY_INI = os.path.join(SUB_DATA_DIR, 'cp2k_proc.ini')
GOOD_XYZ_ONLY_OUT = os.path.join(SUB_DATA_DIR, 'glu_3.0_1.075_xyz_only_good.xyz')

# For testing catching errors #

MISSING_TEMPLATE_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_miss_file.ini')
CUTOFF_CP2K_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_cutoff.ini')
TOO_FEW_CP2K_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_too_few.ini')
TOO_MANY_CP2K_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_too_many.ini')
NO_FILES_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_no_files.ini')
MISSING_KEY_INI = os.path.join(SUB_DATA_DIR, 'bad_cp2k2data_missing_key.ini')


class TestCP2KProcFailWell(unittest.TestCase):

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


class TestCP2KProc(unittest.TestCase):
    def testHelpOption(self):
        test_input = ["-h"]
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)
        with capture_stderr(main, test_input) as output:
            self.assertEqual(len(output), 0)

    def testOneFileToDataXYZ(self):
        # When checking output, ignore differences in version and time
        try:
            main(["-c", ONE_2DATA_INI])
            diffs = diff_lines(GLU_DATA_OUT, GOOD_GLU_DATA_OUT)
            self.assertEqual(len(diffs), 2)
            self.assertTrue("Created on " in diffs[0])
            self.assertFalse(diff_lines(GLU_XYZ_OUT, GOOD_GLU_XYZ_OUT))
        finally:
            silent_remove(GLU_DATA_OUT, disable=DISABLE_REMOVE)
            silent_remove(GLU_XYZ_OUT, disable=DISABLE_REMOVE)

    def testFileListToData(self):
        try:
            silent_remove(GLU_DATA_OUT)
            test_input = ["-c", MULT_2DATA_INI]
            main(test_input)
            diffs = diff_lines(GLU_DATA_OUT, GOOD_GLU_DATA_OUT)
            diffs1 = diff_lines(GLU_DATA_OUT2, GOOD_GLU_DATA_OUT2)
            for diff_list in [diffs, diffs1]:
                self.assertEqual(len(diff_list), 2)
                self.assertTrue("Created on " in diff_list[0])
        finally:
            silent_remove(GLU_DATA_OUT, disable=DISABLE_REMOVE)
            silent_remove(GLU_DATA_OUT1, disable=DISABLE_REMOVE)
            silent_remove(GLU_DATA_OUT2, disable=DISABLE_REMOVE)

    def testMultFileToPDBXYZ(self):
        # When checking output, ignore differences in version and time
        try:
            test_input = ["-c", MULT_2PDB_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue('"tests/test_data/cp2k_proc/glu_2.5_1.0.out",-283.341542,"False","False"' in output)
                self.assertTrue('"tests/test_data/cp2k_proc/glu_2.5_1.05-1.out",-283.526959,"True","True"' in output)
            diffs = diff_lines(GLU_PDB_OUT, GOOD_GLU_PDB_OUT)
            diffs1 = diff_lines(GLU_PDB_OUT2, GOOD_GLU_PDB_OUT2)
            for diff_list in [diffs, diffs1]:
                self.assertEqual(len(diff_list), 2)
                self.assertTrue("Created on " in diff_list[0])
            self.assertFalse(diff_lines(GLU_XYZ_OUT, GOOD_GLU_XYZ_OUT))
        finally:
            silent_remove(GLU_PDB_OUT, disable=DISABLE_REMOVE)
            silent_remove(GLU_PDB_OUT1, disable=DISABLE_REMOVE)
            silent_remove(GLU_PDB_OUT2, disable=DISABLE_REMOVE)
            silent_remove(GLU_XYZ_OUT, disable=DISABLE_REMOVE)
            silent_remove(GLU_XYZ_OUT1, disable=DISABLE_REMOVE)
            silent_remove(GLU_XYZ_OUT2, disable=DISABLE_REMOVE)

    def testXYZOnly(self):
        # When checking output, ignore differences in version and time
        try:
            test_input = ["-c", XYZ_ONLY_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue('"file_name","qmmm_energy","opt_complete","job_complete"\n'
                                '"tests/test_data/cp2k_proc/glu_3.0_1.075.out",-472.455098,"NA","True"' in output)
            with capture_stderr(main, test_input) as output:
                self.assertTrue("Did not find the element type" in output)
            self.assertFalse(diff_lines(GLU_XYZ_OUT, GOOD_XYZ_ONLY_OUT))
        finally:
            silent_remove(GLU_XYZ_OUT, disable=DISABLE_REMOVE)
