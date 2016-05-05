import unittest
import os

from md_utils.data_edit import main
from md_utils.md_common import diff_lines, silent_remove, capture_stderr, capture_stdout

__author__ = 'hmayes'

# Directories #

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'data_edit')

# Input files #

DEF_INI = os.path.join(SUB_DATA_DIR, 'data_reorder.ini')
SERCA_INI = os.path.join(SUB_DATA_DIR, 'data_reorder_serca.ini')
BAD_DICT_INI = os.path.join(SUB_DATA_DIR, 'data_reorder_bad_dict.ini')
GLUP_INI = os.path.join(SUB_DATA_DIR, 'data_reorder_glup_glue.ini')
IMP_ATOMS_BAD_INI = os.path.join(SUB_DATA_DIR, 'data_print_impt_atoms_bad_input.ini')
IMP_ATOMS_TYPO_INI = os.path.join(SUB_DATA_DIR, 'data_print_impt_atoms_key_typo.ini')
GLUE_GLUP_IMP_ATOMS_INI = os.path.join(SUB_DATA_DIR, 'data_print_impt_atoms.ini')
GLUE_GLUP_OWN_ATOMS_INI = os.path.join(SUB_DATA_DIR, 'data_print_own_atoms.ini')
RETYPE_INI = os.path.join(SUB_DATA_DIR, 'data_retype.ini')
BAD_DATA_INI = os.path.join(SUB_DATA_DIR, 'data_reorder_bad_data.ini')
SORT_INI = os.path.join(SUB_DATA_DIR, 'data_sort.ini')

# Output files

# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(SUB_DATA_DIR, '4.25_new.data')
GOOD_OUT = os.path.join(SUB_DATA_DIR, '4.25_new_good.data')
# noinspection PyUnresolvedReferences
SERCA_0_OUT = os.path.join(SUB_DATA_DIR, 'reus_0_edited_new.data')
SERCA_0_GOOD_OUT = os.path.join(SUB_DATA_DIR, 'reus_0_edited_new_good.data')
# noinspection PyUnresolvedReferences
SERCA_1_OUT = os.path.join(SUB_DATA_DIR, 'reus_1_edited_new.data')
SERCA_1_GOOD_OUT = os.path.join(SUB_DATA_DIR, 'reus_1_edited_new_good.data')
# noinspection PyUnresolvedReferences
GLUP_OUT = os.path.join(SUB_DATA_DIR, 'glup_autopsf_new.data')
GLUP_GOOD_OUT = os.path.join(SUB_DATA_DIR, 'glup_autopsf_new_good.data')
# noinspection PyUnresolvedReferences
GLUE_SELECT_OUT = os.path.join(SUB_DATA_DIR, 'glu_deprot_selected.txt')
GLUE_SELECT_OUT_GOOD = os.path.join(SUB_DATA_DIR, 'glu_deprot_selected_good.txt')
GLUE_SELECT_OWN_OUT_GOOD = os.path.join(SUB_DATA_DIR, 'glu_deprot_selected_owned_good.txt')
# noinspection PyUnresolvedReferences
GLUP_SELECT_OUT = os.path.join(SUB_DATA_DIR, 'glup_autopsf_new_good_selected.txt')
GLUP_SELECT_OUT_GOOD = os.path.join(SUB_DATA_DIR, 'glup_autopsf_new_good_selected_good.txt')
GLUP_SELECT_OWN_OUT_GOOD = os.path.join(SUB_DATA_DIR, 'glup_autopsf_new_good_selected_owned_good.txt')
# noinspection PyUnresolvedReferences
GLUP_RETYPE_OUT = os.path.join(SUB_DATA_DIR, 'glup_autopsf_reordered_to_retype_new.data')
GLUP_RETYPE_OUT_GOOD = os.path.join(SUB_DATA_DIR, 'glup_autopsf_reordered_retyped_good.data')
# noinspection PyUnresolvedReferences
GLUP_SORT_OUT = os.path.join(SUB_DATA_DIR, 'glup_new_new.data')
GLUP_SORT_OUT_GOOD = os.path.join(SUB_DATA_DIR, 'glup_new_sorted.data')


class TestDataEdit(unittest.TestCase):

    def testNoArgs(self):
        with capture_stderr(main, []) as output:
            self.assertTrue("Could not read file" in output)
        with capture_stdout(main, []) as output:
            self.assertTrue("optional arguments" in output)

    def testDefIni(self):
        try:
            main(["-c", DEF_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT)

    def testSerca(self):
        """
        Tests on another set of data, and a bad file location
        """
        with capture_stderr(main, ["-c", SERCA_INI]) as output:
            self.assertTrue("No such file or directory" in output)
            self.assertFalse(diff_lines(SERCA_0_OUT, SERCA_0_GOOD_OUT))
            self.assertFalse(diff_lines(SERCA_1_OUT, SERCA_1_GOOD_OUT))
            silent_remove(SERCA_0_OUT)
            silent_remove(SERCA_1_OUT)

    def testBadDict(self):
        with capture_stderr(main, ["-c", BAD_DICT_INI]) as output:
            self.assertTrue("Expected exactly two comma-separated values" in output)
        silent_remove(DEF_OUT)

    def testGlupIni(self):
        try:
            main(["-c", GLUP_INI])
            self.assertFalse(diff_lines(GLUP_OUT, GLUP_GOOD_OUT))
        finally:
            silent_remove(GLUP_OUT)

    def testImptAtomsBadInput(self):
        with capture_stderr(main, ["-c", IMP_ATOMS_BAD_INI]) as output:
            self.assertTrue("Problem with config vals on key print_dihedral_types: invalid literal for int()" in output)


    def testImptAtoms(self):
        try:
            main(["-c", GLUE_GLUP_IMP_ATOMS_INI])
            self.assertFalse(diff_lines(GLUE_SELECT_OUT, GLUE_SELECT_OUT_GOOD))
            self.assertFalse(diff_lines(GLUP_SELECT_OUT, GLUP_SELECT_OUT_GOOD))
        finally:
            [silent_remove(o_file) for o_file in [GLUE_SELECT_OUT, GLUP_SELECT_OUT]]

    def testOwnAtoms(self):
        try:
            main(["-c", GLUE_GLUP_OWN_ATOMS_INI])
            self.assertFalse(diff_lines(GLUE_SELECT_OUT, GLUE_SELECT_OWN_OUT_GOOD))
            self.assertFalse(diff_lines(GLUP_SELECT_OUT, GLUP_SELECT_OWN_OUT_GOOD))
        finally:
            [silent_remove(o_file) for o_file in [GLUE_SELECT_OUT, GLUP_SELECT_OUT]]

    def testKeyTypo(self):
        with capture_stderr(main, ["-c", IMP_ATOMS_TYPO_INI]) as output:
            self.assertTrue("Unexpected key 'print_interaction_involving_atoms' in configuration" in output)

    def testBadData(self):
        # main(["-c", BAD_DATA_INI])
        with capture_stderr(main, ["-c", BAD_DATA_INI]) as output:
            self.assertTrue("Problems reading data" in output)

    def testRetype(self):
        try:
            main(["-c", RETYPE_INI])
            self.assertFalse(diff_lines(GLUP_RETYPE_OUT, GLUP_RETYPE_OUT_GOOD))
            # for debugging:
            # with open(GLUP_RETYPE_OUT) as f:
            #     with open(GLUP_RETYPE_OUT_GOOD) as g:
            #         for d_line, g_line in zip(f, g):
            #             if d_line.strip() != g_line.strip():
            #                 print(d_line.strip())
            #                 print(g_line.strip())
        finally:
            silent_remove(GLUP_RETYPE_OUT)

    def testSort(self):
        try:
            main(["-c", SORT_INI])
            # with open(GLUP_SORT_OUT) as f:
            #     with open(GLUP_SORT_OUT_GOOD) as g:
            #         for d_line, g_line in zip(f, g):
            #             if d_line.strip() != g_line.strip():
            #                 print(d_line.strip())
            #                 print(g_line.strip())
            self.assertFalse(diff_lines(GLUP_SORT_OUT, GLUP_SORT_OUT_GOOD))
        finally:
            silent_remove(GLUP_SORT_OUT)
            # pass

