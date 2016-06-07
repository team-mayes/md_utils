import logging
import unittest
import os

from md_utils import data2data
from md_utils.md_common import diff_lines, silent_remove, capture_stderr, capture_stdout

logger = logging.getLogger('data2data')
logging.basicConfig(filename='data2data.log', filemode='w', level=logging.DEBUG)

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

# For comparison:
GLU_DEPROT_DATA = os.path.join(SUB_DATA_DIR, 'glu_deprot.data')


class TestData2Data(unittest.TestCase):
    def testNoDefault(self):
        with capture_stderr(data2data.main, []) as output:
            self.assertTrue("Could not read file" in output)
        with capture_stdout(data2data.main, []) as output:
            self.assertTrue("optional arguments" in output)

    def testSerca(self):
        try:
            data2data.main(["-c", SERCA_INI])
            self.assertFalse(diff_lines(SERCA_OUT, SERCA_GOOD_OUT))
        finally:
            silent_remove(SERCA_OUT)

    def testReordGluDeprot(self):
        """
        Tests that can handle an emtpy line in the data file and make a data number dictionary
        """
        try:
            data2data.main(["-c", REORD_GLU_INI])
            self.assertFalse(diff_lines(GLU_DEPROT_ATOM_NUM_DICT, GLU_DEPROT_ATOM_NUM_DICT_GOOD))
            # for debugging:
            # with open(GLU_DEPROT_OUT) as f:
            #     with open(GLU_DEPROT_DATA) as g:
            #         for d_line, g_line in zip(f, g):
            #             if d_line.strip() != g_line.strip():
            #                 print(d_line.strip())
            #                 print(g_line.strip())
        finally:
            silent_remove(GLU_DEPROT_OUT)
            silent_remove(GLU_DEPROT_ATOM_NUM_DICT)

    def testMissingDataFile(self):
        with capture_stderr(data2data.main, ["-c", MISSING_DATA_INI]) as output:
            self.assertTrue("No such file or directory" in output)

    def testMissingConfigKey(self):
        with capture_stderr(data2data.main, ["-c", MISSING_KEY_INI]) as output:
            self.assertTrue("Input data missing: 'Missing config val for key data_tpl_file'" in output)

    def testAtomNumTypeDict(self):
        try:
            data2data.main(["-c", GLUE_GLUP_INI])
            self.assertFalse(diff_lines(GLUP_GLUE_ATOM_NUM_DICT, GLUP_GLUE_ATOM_NUM_DICT_GOOD))
            self.assertFalse(diff_lines(GLUP_GLUE_ATOM_TYPE_DICT, GLUP_GLUE_ATOM_TYPE_DICT_GOOD))
            self.assertFalse(diff_lines(GLUP_AS_GLUE, GLUP_AS_GLUE_GOOD))
        finally:
            silent_remove(GLUP_GLUE_ATOM_NUM_DICT)
            silent_remove(GLUP_GLUE_ATOM_TYPE_DICT)
            silent_remove(GLUP_AS_GLUE)

    def testGlupMismatch(self):
        with capture_stderr(data2data.main, ["-c", GLUP_MISMATCH_INI]) as output:
            self.assertTrue("Problems reading data" in output)

    def testGlupDictMismatch(self):
        with capture_stderr(data2data.main, ["-c", GLUP_MISMATCH_DICT_INI]) as output:
            self.assertTrue("Problems reading data" in output)
            self.assertTrue("Previously matched" in output)

    def testGluSercaMismatch(self):
        with capture_stderr(data2data.main, ["-c", GLUE_SERCA_INI]) as output:
            self.assertTrue("atoms in the template file (1429) does not equal the number of atoms (214084)" in output)

    def testGluSercaDictMismatch(self):
        with capture_stderr(data2data.main, ["-c", GLUE_SERCA_DICT_INI]) as output:
            self.assertTrue("Number of atoms (214084) in the file" in output)
            self.assertTrue("atoms (1429) in the template file" in output)
        # try:
        #     data2data.main(["-c", ])
        # finally:
        #     pass
