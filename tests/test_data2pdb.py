import json
import logging
import unittest
import os

from md_utils import data2pdb
from md_utils.md_common import diff_lines, silent_remove

logger = logging.getLogger('data2pdb')
logging.basicConfig(filename='data2pdb.log', filemode='w', level=logging.DEBUG)

__author__ = 'hmayes'

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'data2pdb')
DEF_INI = os.path.join(SUB_DATA_DIR, 'data2pdb.ini')
GLU_INI = os.path.join(SUB_DATA_DIR, 'data2pdb_glu.ini')
GLU_DICT_INI = os.path.join(SUB_DATA_DIR, 'data2pdb_glu_dict.ini')

PDB_TPL = os.path.join(SUB_DATA_DIR, 'glue_hm_tpl.pdb')
# noinspection PyUnresolvedReferences
PDB_TPL_OUT = os.path.join(SUB_DATA_DIR, 'reproduced_tpl.pdb')

# noinspection PyUnresolvedReferences
PDB_OUT = os.path.join(SUB_DATA_DIR, 'glue_hm.pdb')
GOOD_PDB_OUT = os.path.join(SUB_DATA_DIR, 'glue_hm_good.pdb')

# noinspection PyUnresolvedReferences
GLU_OUT = os.path.join(SUB_DATA_DIR, '0.625_20c_reorder_retype_548990.pdb')
GOOD_GLU_OUT = os.path.join(SUB_DATA_DIR, '0.625_20c_reorder_retype_548990_good.pdb')

DEF_DICT_OUT = os.path.join(TEST_DIR, 'atom_dict.json')
GOOD_DICT = os.path.join(SUB_DATA_DIR, 'atom_dict_good.json')


class TestDumpEdit(unittest.TestCase):

    def testDefIni(self):
        try:
            data2pdb.main(["-c", DEF_INI])
            # for debugging:
            # with open(PDB_TPL) as f:
            #     with open(PDB_TPL_OUT) as g:
            #         for d_line, g_line in zip(f, g):
            #             if d_line.strip() != g_line.strip():
            #                 print(d_line.strip())
            #                 print(g_line.strip())

            # will only be there is debugging is on
            if os.path.exists(PDB_TPL_OUT):
                self.assertFalse(diff_lines(PDB_TPL_OUT, PDB_TPL))
            self.assertFalse(diff_lines(PDB_OUT, GOOD_PDB_OUT))
        finally:
            silent_remove(PDB_TPL_OUT)
            silent_remove(PDB_OUT)
            pass

    def testGlu(self):
        try:
            data2pdb.main(["-c", GLU_INI])
            self.assertFalse(diff_lines(GLU_OUT, GOOD_GLU_OUT))
        finally:
            silent_remove(PDB_TPL_OUT)
            silent_remove(GLU_OUT)

    def testGluDict(self):
        try:
            data2pdb.main(["-c", GLU_DICT_INI])
            self.assertFalse(diff_lines(GLU_OUT, GOOD_GLU_OUT))
            with open(DEF_DICT_OUT, 'r') as d_file:
                dict_test = json.load(d_file)
            with open(GOOD_DICT, 'r') as d_file:
                dict_good = json.load(d_file)
            self.assertEqual(dict_test, dict_good)
        finally:
            silent_remove(PDB_TPL_OUT)
            silent_remove(GLU_OUT)
            silent_remove(DEF_DICT_OUT)
