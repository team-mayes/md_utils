import unittest
import os

from md_utils.pdb_edit import main, read_int_dict
from md_utils.md_common import diff_lines, capture_stderr, silent_remove

__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'pdb_edit')
ATOM_DICT_FILE = os.path.join(SUB_DATA_DIR, 'atom_reorder.csv')
DEF_INI = os.path.join(SUB_DATA_DIR, 'pdb_edit.ini')
ATOM_DICT_BAD_INI = os.path.join(SUB_DATA_DIR, 'pdb_edit_bad_reorder.ini')
UNEXPECTED_KEY_INI = os.path.join(SUB_DATA_DIR, 'pdb_edit_wrong_key.ini')
ATOM_DICT_REPEAT_INI = os.path.join(SUB_DATA_DIR, 'pdb_edit_repeat_key.ini')
MOL_CHANGE_INI = os.path.join(SUB_DATA_DIR, 'pdb_edit_mol_change.ini')
MOL_CHANGE_RENUM_INI = os.path.join(SUB_DATA_DIR, 'pdb_edit_mol_renum.ini')
# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(SUB_DATA_DIR, 'new.pdb')
GOOD_OUT = os.path.join(SUB_DATA_DIR, 'glue_autopsf_short_good.pdb')
GOOD_MOL_CHANGE_OUT = os.path.join(SUB_DATA_DIR, 'glue_autopsf_short_mol_change_good.pdb')
GOOD_MOL_CHANGE_RENUM_OUT = os.path.join(SUB_DATA_DIR, 'glue_autopsf_short_mol_change_renum_good.pdb')

ADD_ELEMENT_INI = os.path.join(SUB_DATA_DIR, 'pdb_edit_add_element.ini')
ADD_ELEMENT_OUT = os.path.join(SUB_DATA_DIR, 'glue_autopsf_short_no_elements_new.pdb')
GOOD_ADD_ELEMENT_OUT = os.path.join(SUB_DATA_DIR, 'glue_autopsf_short.pdb')


GOOD_ATOM_DICT = {1: 20, 2: 21, 3: 22, 4: 23, 5: 24, 6: 25, 7: 26, 8: 27, 9: 2, 10: 1, 11: 3, 12: 4, 13: 5, 14: 6,
                  15: 7, 16: 8, 17: 9, 18: 10, 19: 11, 20: 12, 21: 13, 22: 14, 23: 15, 24: 16, 25: 17, 26: 18, 27: 19}


class TestPDBEditFunctions(unittest.TestCase):
    def testReadAtomNumDict(self):
        # Will renumber atoms and then sort them
        test_dict = read_int_dict(ATOM_DICT_FILE)
        self.assertEqual(test_dict, GOOD_ATOM_DICT)


class TestPDBEditMain(unittest.TestCase):
    # Testing normal function; can use inputs here as examples
    def testReorderAtoms(self):
        try:
            main(["-c", DEF_INI])
            # for debugging:
            # with open(DEF_OUT) as f:
            #     with open(GOOD_OUT) as g:
            #         for d_line, g_line in zip(f, g):
            #             if d_line != g_line:
            #                 print(d_line, g_line)
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT)

    def testChangeMol(self):
        try:
            main(["-c", MOL_CHANGE_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_MOL_CHANGE_OUT))
        finally:
            silent_remove(DEF_OUT)
            # pass

    def testChangeRenumMol(self):
        try:
            main(["-c", MOL_CHANGE_RENUM_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_MOL_CHANGE_RENUM_OUT))
        finally:
            silent_remove(DEF_OUT)

    def testAddElements(self):
        try:
            main(["-c", ADD_ELEMENT_INI])
            self.assertFalse(diff_lines(ADD_ELEMENT_OUT, GOOD_ADD_ELEMENT_OUT))
        finally:
            silent_remove(ADD_ELEMENT_OUT)
            # pass


class TestPDBEditCatchImperfectInput(unittest.TestCase):
    # Testing for elegant failure and hopefully helpful error messages
    def testUnexpectedKey(self):
        # main(["-c", UNEXPECTED_KEY_INI])
        with capture_stderr(main, ["-c", UNEXPECTED_KEY_INI]) as output:
            self.assertTrue("Unexpected key" in output)

    def testRepeatKeyNumDict(self):
        # main(["-c", ATOM_DICT_REPEAT_INI])
        with capture_stderr(main, ["-c", ATOM_DICT_REPEAT_INI]) as output:
            self.assertTrue("non-unique" in output)

    def testReadBadAtomNumDict(self):
        # main(["-c", ATOM_DICT_BAD_INI])
        with capture_stderr(main, ["-c", ATOM_DICT_BAD_INI]) as output:
            self.assertTrue("xx" in output)
            self.assertTrue("26" in output)
            self.assertTrue("Problems with input information" in output)
