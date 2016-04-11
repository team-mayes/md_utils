import json
import logging
import unittest
import os

from md_utils import data2data
from md_utils.md_common import diff_lines, silent_remove

logger = logging.getLogger('data2data')
logging.basicConfig(filename='data2data.log', filemode='w', level=logging.DEBUG)

__author__ = 'hmayes'

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'data2data')

# Input files
DEF_INI = os.path.join(SUB_DATA_DIR, 'data2data.ini')
SERCA_INI = os.path.join(SUB_DATA_DIR, 'data2data_serca.ini')
REORD_GLU_INI = os.path.join(SUB_DATA_DIR, 'data2data_glu_deprot.ini')

# Output files
# noinspection PyUnresolvedReferences
SERCA_OUT = os.path.join(SUB_DATA_DIR, 'serca_reus_2_edited_ord_new.data')
SERCA_GOOD_OUT = os.path.join(SUB_DATA_DIR, 'serca_reus_2_edited_ord_new_good.data')
# noinspection PyUnresolvedReferences
GLU_DEPROT_OUT = os.path.join(SUB_DATA_DIR, 'glu_deprot_switched_order_for_dict_new.data')
GLU_DEPROT_ATOM_DICT = os.path.join(SUB_DATA_DIR, 'glu_deprot_atom_num_dict_old_new.csv')
GLU_DEPROT_ATOM_DICT_GOOD = os.path.join(SUB_DATA_DIR, 'glu_deprot_atom_num_dict_old_new_good.csv')

# For comparison:
GLU_DEPROT_DATA = os.path.join(SUB_DATA_DIR, 'glu_deprot.data')


class TestData2Data(unittest.TestCase):

    def testDefIni(self):
        try:
            data2data.main(["-c", DEF_INI])
        finally:
            # silent_remove(PDB_OUT)
            pass

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
            self.assertFalse(diff_lines(GLU_DEPROT_ATOM_DICT, GLU_DEPROT_ATOM_DICT_GOOD))
            # for debugging:
            # with open(GLU_DEPROT_OUT) as f:
            #     with open(GLU_DEPROT_DATA) as g:
            #         for d_line, g_line in zip(f, g):
            #             if d_line.strip() != g_line.strip():
            #                 print(d_line.strip())
            #                 print(g_line.strip())
        finally:
            silent_remove(GLU_DEPROT_OUT)
            silent_remove(GLU_DEPROT_ATOM_DICT)
