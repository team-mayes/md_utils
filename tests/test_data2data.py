import logging
import unittest
import os

from md_utils.data2data import main
from md_utils.md_common import (diff_lines, silent_remove, capture_stderr, capture_stdout)

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'

# Directories #

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'data2data')

# Input files #

SERCA_INI = os.path.join(SUB_DATA_DIR, 'data2data_serca.ini')
REORD_GLU_INI = os.path.join(SUB_DATA_DIR, 'data2data_glu_deprot.ini')
MISSING_DATA_INI = os.path.join(SUB_DATA_DIR, 'data2data_missing_data_file.ini')
MISSING_KEY_INI = os.path.join(SUB_DATA_DIR, 'data2data_missing_req_key.ini')
GLUE_GLUP_INI = os.path.join(SUB_DATA_DIR, 'data2data_glue_glup.ini')
GLUP_MISMATCH_INI = os.path.join(SUB_DATA_DIR, 'data2data_glup_mismatch.ini')
GLUP_MISMATCH_DICT_INI = os.path.join(SUB_DATA_DIR, 'data2data_glup_mismatch_dict.ini')
GLUE_SERCA_INI = os.path.join(SUB_DATA_DIR, 'data2data_glue_serca.ini')
GLUE_SERCA_DICT_INI = os.path.join(SUB_DATA_DIR, 'data2data_glue_serca_dict.ini')

# Output files #

# noinspection PyUnresolvedReferences
SERCA_OUT = os.path.join(SUB_DATA_DIR, 'serca_reus_2_edited_ord_new.data')
SERCA_GOOD_OUT = os.path.join(SUB_DATA_DIR, 'serca_reus_2_edited_ord_new_good.data')
# noinspection PyUnresolvedReferences
GLU_DEPROT_OUT = os.path.join(SUB_DATA_DIR, 'glu_deprot_switched_order_for_dict_new.data')
# noinspection PyUnresolvedReferences
GLU_DEPROT_ATOM_NUM_DICT = os.path.join(SUB_DATA_DIR, 'glu_deprot_atom_num_dict_old_new.csv')
GLU_DEPROT_ATOM_NUM_DICT_GOOD = os.path.join(SUB_DATA_DIR, 'glu_deprot_atom_num_dict_old_new_good.csv')

# noinspection PyUnresolvedReferences
GLUP_AS_GLUE = os.path.join(SUB_DATA_DIR, 'glup_reordered_new.data')
GLUP_AS_GLUE_GOOD = os.path.join(SUB_DATA_DIR, 'glup_reordered_new_good.data')
# noinspection PyUnresolvedReferences
GLUP_GLUE_ATOM_NUM_DICT = os.path.join(SUB_DATA_DIR, 'glup_glue_atom_num_dict_old_new.csv')
GLUP_GLUE_ATOM_NUM_DICT_GOOD = os.path.join(SUB_DATA_DIR, 'glup_glue_atom_num_dict_old_new_good.csv')
# noinspection PyUnresolvedReferences
GLUP_GLUE_ATOM_TYPE_DICT = os.path.join(SUB_DATA_DIR, 'glup_glue_atom_type_dict_old_new.csv')
GLUP_GLUE_ATOM_TYPE_DICT_GOOD = os.path.join(SUB_DATA_DIR, 'glup_glue_atom_type_dict_old_new_good.csv')

GLU_ADJUST_ATOM_INI = os.path.join(SUB_DATA_DIR, 'data2data_change_xyz.ini')
GLU_ADJUST_ATOM_NEG_INT_INI = os.path.join(SUB_DATA_DIR, 'data2data_change_xyz_neg_int.ini')
GLU_ADJUST_ATOM_NON_INT_INI = os.path.join(SUB_DATA_DIR, 'data2data_change_xyz_not_int.ini')
GLU_ADJUST_ATOM_NO_STEPS_INI = os.path.join(SUB_DATA_DIR, 'data2data_change_xyz_zero_steps.ini')
GLU_ADJUST_ATOM_TOO_FEW_INI = os.path.join(SUB_DATA_DIR, 'data2data_change_xyz_too_few.ini')
GLU_ADJUST_ATOM_TOO_LARGE_INT_INI = os.path.join(SUB_DATA_DIR, 'data2data_change_xyz_too_large_int.ini')

GLU_ADJUST_TPL = os.path.join(SUB_DATA_DIR, '1.250_prot_min.data')
GLU_ADJUST_OUT_NEG1 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_-1.data')
GOOD_GLU_ADJUST_OUT_NEG1 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_-1_good.data')
GLU_ADJUST_OUT_0 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_0.data')
GLU_ADJUST_OUT_1 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_1.data')
GOOD_GLU_ADJUST_OUT_1 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_1_good.data')
GLU_ADJUST_OUT_2 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_2.data')
GOOD_GLU_ADJUST_OUT_2 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_2_good.data')

# For comparison:
GLU_DEPROT_DATA = os.path.join(SUB_DATA_DIR, 'glu_deprot.data')

GLU_DIST_INI = os.path.join(SUB_DATA_DIR, 'data2data_set_distance.ini')
GLU_DIST_OUT = os.path.join(SUB_DATA_DIR, '1.250_prot_min_2.6.data')
GOOD_GLU_DIST_OUT = os.path.join(SUB_DATA_DIR, '1.250_prot_min_2.6_good.data')

GLU_DIST_ONE_ATOM_INI = os.path.join(SUB_DATA_DIR, 'data2data_set_dist_one_atom.ini')

GLU_MULT_DIST_INI = os.path.join(SUB_DATA_DIR, 'data2data_set_dist_mult.ini')
GLU_MULT_DIST_OUT1 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_0.95.data')
GOOD_GLU_MULT_DIST_OUT1 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_0.95_good.data')
GLU_MULT_DIST_OUT2 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_1.0.data')
GOOD_GLU_MULT_DIST_OUT2 = os.path.join(SUB_DATA_DIR, '1.250_prot_min_1.0_good.data')


class TestData2DataFailWell(unittest.TestCase):
    def testNoDefault(self):
        with capture_stderr(main, []) as output:
            self.assertTrue("Could not read file" in output)
        with capture_stdout(main, []) as output:
            self.assertTrue("optional arguments" in output)

    def testMissingDataFile(self):
        with capture_stderr(main, ["-c", MISSING_DATA_INI]) as output:
            self.assertTrue("No such file or directory" in output)

    def testMissingConfigKey(self):
        test_input = ["-c", MISSING_KEY_INI]
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Missing config val for key 'data_tpl_file'" in output)

    def testGlupMismatch(self):
        with capture_stderr(main, ["-c", GLUP_MISMATCH_INI]) as output:
            self.assertTrue("Problems reading data" in output)

    def testGlupDictMismatch(self):
        with capture_stderr(main, ["-c", GLUP_MISMATCH_DICT_INI]) as output:
            self.assertTrue("Problems reading data" in output)
            self.assertTrue("Previously matched" in output)

    def testGluSercaMismatch(self):
        with capture_stderr(main, ["-c", GLUE_SERCA_INI]) as output:
            self.assertTrue("atoms in the template file (1429) does not equal the number of atoms (214084)" in output)

    def testGluSercaDictMismatch(self):
        with capture_stderr(main, ["-c", GLUE_SERCA_DICT_INI]) as output:
            self.assertTrue("Number of atoms (214084) in the file" in output)
            self.assertTrue("atoms (1429) in the template file" in output)

    def testAdjustAtomNegInt(self):
        test_input = ["-c", GLU_ADJUST_ATOM_NEG_INT_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("keyword must be a positive integer" in output)

    def testAdjustAtomNonInt(self):
        test_input = ["-c", GLU_ADJUST_ATOM_NON_INT_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("keyword must be a positive integer" in output)

    def testAdjustAtomZeroSteps(self):
        test_input = ["-c", GLU_ADJUST_ATOM_NO_STEPS_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("positive number of steps" in output)

    def testAdjustAtomTooFewXYZ(self):
        test_input = ["-c", GLU_ADJUST_ATOM_TOO_FEW_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("comma-separated list" in output)

    def testAdjustAtomTooLargeInt(self):
        test_input = ["-c", GLU_ADJUST_ATOM_TOO_LARGE_INT_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("found only" in output)

    def testSetDistOneAtom(self):
        test_input = ["-c", GLU_DIST_ONE_ATOM_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("WARNING:  Use the 'atoms_dist' keyword" in output)


class TestData2Data(unittest.TestCase):
    def testSerca(self):
        try:
            main(["-c", SERCA_INI])
            self.assertFalse(diff_lines(SERCA_OUT, SERCA_GOOD_OUT))
        finally:
            silent_remove(SERCA_OUT, disable=DISABLE_REMOVE)

    def testReordGluDeprot(self):
        """
        Tests that can handle an emtpy line in the data file and make a data number dictionary
        """
        try:
            main(["-c", REORD_GLU_INI])
            self.assertFalse(diff_lines(GLU_DEPROT_ATOM_NUM_DICT, GLU_DEPROT_ATOM_NUM_DICT_GOOD))
        finally:
            silent_remove(GLU_DEPROT_OUT)
            silent_remove(GLU_DEPROT_ATOM_NUM_DICT)

    def testAtomNumTypeDict(self):
        try:
            main(["-c", GLUE_GLUP_INI])
            self.assertFalse(diff_lines(GLUP_GLUE_ATOM_NUM_DICT, GLUP_GLUE_ATOM_NUM_DICT_GOOD))
            self.assertFalse(diff_lines(GLUP_GLUE_ATOM_TYPE_DICT, GLUP_GLUE_ATOM_TYPE_DICT_GOOD))
            self.assertFalse(diff_lines(GLUP_AS_GLUE, GLUP_AS_GLUE_GOOD, delimiter=" "))
        finally:
            silent_remove(GLUP_GLUE_ATOM_NUM_DICT, disable=DISABLE_REMOVE)
            silent_remove(GLUP_GLUE_ATOM_TYPE_DICT, disable=DISABLE_REMOVE)
            silent_remove(GLUP_AS_GLUE, disable=DISABLE_REMOVE)

    def testAdjustAtom(self):
        try:
            main(["-c", GLU_ADJUST_ATOM_INI])
            self.assertFalse(diff_lines(GLU_ADJUST_OUT_0, GLU_ADJUST_TPL))
            self.assertFalse(diff_lines(GLU_ADJUST_OUT_NEG1, GOOD_GLU_ADJUST_OUT_NEG1))
            self.assertFalse(diff_lines(GLU_ADJUST_OUT_1, GOOD_GLU_ADJUST_OUT_1))
            self.assertFalse(diff_lines(GLU_ADJUST_OUT_2, GOOD_GLU_ADJUST_OUT_2))
        finally:
            silent_remove(GLU_ADJUST_OUT_NEG1, disable=DISABLE_REMOVE)
            silent_remove(GLU_ADJUST_OUT_0, disable=DISABLE_REMOVE)
            silent_remove(GLU_ADJUST_OUT_1, disable=DISABLE_REMOVE)
            silent_remove(GLU_ADJUST_OUT_2, disable=DISABLE_REMOVE)

    def testSetDist(self):
        try:
            main(["-c", GLU_DIST_INI])
            self.assertFalse(diff_lines(GLU_DIST_OUT, GOOD_GLU_DIST_OUT))
        finally:
            silent_remove(GLU_DIST_OUT)

    def testSetDistMult(self):
        try:
            main(["-c", GLU_MULT_DIST_INI])
            self.assertFalse(diff_lines(GLU_MULT_DIST_OUT1, GOOD_GLU_MULT_DIST_OUT1))
            self.assertFalse(diff_lines(GLU_MULT_DIST_OUT2, GOOD_GLU_MULT_DIST_OUT2))
        finally:
            silent_remove(GLU_MULT_DIST_OUT1)
            silent_remove(GLU_MULT_DIST_OUT2)
