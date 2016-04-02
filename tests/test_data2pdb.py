import unittest
import os

from md_utils import data2pdb
from md_utils.md_common import diff_lines, silent_remove


__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'data2pdb')
DEF_INI = os.path.join(SUB_DATA_DIR, 'data2pdb.ini')
GLU_INI = os.path.join(SUB_DATA_DIR, 'data2pdb_glu.ini')

PDB_TPL = os.path.join(SUB_DATA_DIR, 'glue_hm_tpl.pdb')
# noinspection PyUnresolvedReferences
PDB_TPL_OUT = os.path.join(SUB_DATA_DIR, 'reproduced_tpl.pdb')


# noinspection PyUnresolvedReferences
PDB_OUT = os.path.join(SUB_DATA_DIR, 'glue_hm.pdb')
GOOD_PDB_OUT = os.path.join(SUB_DATA_DIR, 'glue_hm_good.pdb')
# noinspection PyUnresolvedReferences
GLU_OUT = os.path.join(SUB_DATA_DIR, '0.625_20c_100ps_reorder_retype_548990.pdb')
GOOD_GLU_OUT = os.path.join(SUB_DATA_DIR, '0.625_20c_100ps_reorder_retype_548990_good.pdb')

# REPRODUCE_INI = os.path.join(SUB_DATA_DIR, 'dump_edit_reproduce.ini')
# SHORTER_INI = os.path.join(SUB_DATA_DIR, 'dump_shorter.ini')
# SKIP_INI = os.path.join(SUB_DATA_DIR, 'dump_every_2every3.ini')
# REORDER_INI = os.path.join(SUB_DATA_DIR, 'dump_edit.ini')
# REORDER_RENUM_INI = os.path.join(SUB_DATA_DIR, 'dump_renum_mol.ini')
# RETYPE_INI = os.path.join(SUB_DATA_DIR, 'dump_renum_mol_retype.ini')
# DUMP_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_short.dump')

# SHORT_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_4steps.dump')
# SKIP_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_2every3.dump')
# GOOD_ATOM_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_short_reorder_good.dump')


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
            self.assertFalse(diff_lines(PDB_TPL_OUT, PDB_TPL))
            self.assertFalse(diff_lines(PDB_OUT, GOOD_PDB_OUT))
        finally:
            silent_remove(PDB_TPL_OUT)
            silent_remove(PDB_OUT)

    def testGlu(self):
        try:
            data2pdb.main(["-c", GLU_INI])
            self.assertFalse(diff_lines(GLU_OUT, GOOD_GLU_OUT))
        finally:
            silent_remove(PDB_TPL_OUT)
            silent_remove(GLU_OUT)

    # TODO: add recentering option and test
    def testGluRecenter(self):
        try:
            data2pdb.main(["-c", GLU_INI])
            self.assertFalse(diff_lines(GLU_OUT, GOOD_GLU_OUT))
        finally:
            silent_remove(PDB_TPL_OUT)
            silent_remove(GLU_OUT)

