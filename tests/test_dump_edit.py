import unittest
import os

from md_utils import dump_edit
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'dump_edit')
ATOM_DICT_FILE = os.path.join(SUB_DATA_DIR, 'atom_reorder.csv')
DEF_INI = os.path.join(SUB_DATA_DIR, 'dump_edit.ini')
REPRODUCE_INI = os.path.join(SUB_DATA_DIR, 'dump_edit_reproduce.ini')
SHORTER_INI = os.path.join(SUB_DATA_DIR, 'dump_shorter.ini')
SKIP_INI = os.path.join(SUB_DATA_DIR, 'dump_every_2every3.ini')
REORDER_INI = os.path.join(SUB_DATA_DIR, 'dump_edit.ini')
REORDER_RENUM_INI = os.path.join(SUB_DATA_DIR, 'dump_renum_mol.ini')
DUMP_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_short.dump')
DEF_OUT = os.path.join(SUB_DATA_DIR, '0.625_20c_short_reorder.dump')
SHORT_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_4steps.dump')
SKIP_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_2every3.dump')
GOOD_ATOM_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_short_reorder_good.dump')
GOOD_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_short_reorder_good.dump')

# GOOD_OUT = os.path.join(SUB_DATA_DIR, 'glue_autopsf_short_good.pdb')

class TestDumpEdit(unittest.TestCase):

    def testReproduceDump(self):
        try:
            dump_edit.main(["-c", REPRODUCE_INI])
            # for debugging:
            # with open(DEF_OUT) as f:
            #     with open(DUMP_FILE) as g:
            #         for line, gline in zip(f, g):
            #             if line.strip() != gline.strip():
            #                 print(line.strip() == gline.strip(), line.strip(), gline.strip())
            self.assertFalse(diff_lines(DEF_OUT, DUMP_FILE))
        finally:
            silent_remove(DEF_OUT)

    def testFewerSteps(self):
        try:
            dump_edit.main(["-c", SHORTER_INI])
            self.assertFalse(diff_lines(DEF_OUT, SHORT_OUT_FILE))
        finally:
            silent_remove(DEF_OUT)

    def testSkipSteps(self):
        try:
            dump_edit.main(["-c", SKIP_INI])
            self.assertFalse(diff_lines(DEF_OUT, SKIP_OUT_FILE))
        finally:
            silent_remove(DEF_OUT)

    def testReorderAtoms(self):
        try:
            dump_edit.main(["-c", REORDER_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_ATOM_OUT_FILE))
        finally:
            silent_remove(DEF_OUT)

    def testReorderAtomRenumMol(self):
        try:
            dump_edit.main(["-c", REORDER_RENUM_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT_FILE))
        finally:
            silent_remove(DEF_OUT)