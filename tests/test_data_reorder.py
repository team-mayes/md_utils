import unittest
import os

from md_utils import data_reorder
from md_utils.md_common import diff_lines, silent_remove

__author__ = 'hmayes'

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'data_reorder')

# Input files
DEF_INI = os.path.join(SUB_DATA_DIR, 'data_reorder.ini')
SERCA_INI = os.path.join(SUB_DATA_DIR, 'data_reorder_serca.ini')

# Output files

# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(SUB_DATA_DIR, '4.25_ord.data')
GOOD_OUT = os.path.join(SUB_DATA_DIR, '4.25_ord_good.data')

# noinspection PyUnresolvedReferences
SERCA_0_OUT = os.path.join(SUB_DATA_DIR, 'reus_0_edited_ord.data')
SERCA_1_OUT = os.path.join(SUB_DATA_DIR, 'reus_1_edited_ord.data')
SERCA_0_GOOD_OUT = os.path.join(SUB_DATA_DIR, 'reus_0_edited_ord_good.data')
SERCA_1_GOOD_OUT = os.path.join(SUB_DATA_DIR, 'reus_1_edited_ord_good.data')


class TestDataReorder(unittest.TestCase):

    def testDefIni(self):
        try:
            data_reorder.main(["-c", DEF_INI])
            # for debugging:
            # with open(PDB_TPL) as f:
            #     with open(PDB_TPL_OUT) as g:
            #         for d_line, g_line in zip(f, g):
            #             if d_line.strip() != g_line.strip():
            #                 print(d_line.strip())
            #                 print(g_line.strip())
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT)

    def testSerca(self):
        """
        May not cover new parts of code, but at least tests on another set of data
        """
        try:
            data_reorder.main(["-c", SERCA_INI])
            self.assertFalse(diff_lines(SERCA_0_OUT, SERCA_0_GOOD_OUT))
            self.assertFalse(diff_lines(SERCA_1_OUT, SERCA_1_GOOD_OUT))
        finally:
            silent_remove(SERCA_0_OUT)
            silent_remove(SERCA_1_OUT)


    # TODO: test make_atom_type_dict_flag
    #
    # def testGluDict(self):
    #     try:
    #         data_reorder.main(["-c", GLU_DICT_INI])
    #         self.assertFalse(diff_lines(GLU_OUT, GOOD_GLU_OUT))
    #         with open(DEF_DICT_OUT, 'r') as d_file:
    #             dict_test = json.load(d_file)
    #         with open(GOOD_DICT, 'r') as d_file:
    #             dict_good = json.load(d_file)
    #         self.assertEqual(dict_test, dict_good)
    #     finally:
    #         silent_remove(PDB_TPL_OUT)
    #         silent_remove(GLU_OUT)
    #         silent_remove(DEF_DICT_OUT)
