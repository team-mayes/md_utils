import logging
import os
import unittest

from md_utils.md_common import diff_lines, silent_remove, capture_stdout, capture_stderr
from md_utils.psf_edit import main

__author__ = 'hmayes'

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'psf_edit')

DEF_INI = os.path.join(SUB_DATA_DIR, 'psf_edit.ini')
DEF_OUT = os.path.join(SUB_DATA_DIR, 'glue_revised_new.psf')
GOOD_OUT = os.path.join(SUB_DATA_DIR, 'glue_revised.psf')

MOL_DICT_INI = os.path.join(SUB_DATA_DIR, 'psf_edit_mol_dict.ini')

QMMM_OUT_INI = os.path.join(SUB_DATA_DIR, 'psf_make_qmmm_input.ini')
QMMM_OUT = os.path.join(SUB_DATA_DIR, 'amino_id.dat')
GOOD_QMMM_OUT = os.path.join(SUB_DATA_DIR, 'amino_id_good.dat')
VMD_ATOMS_OUT = os.path.join(SUB_DATA_DIR, 'vmd_protein_atoms.dat')
GOOD_VMD_ATOMS_OUT = os.path.join(SUB_DATA_DIR, 'vmd_protein_atoms_good.dat')
MM_KIND_OUT = os.path.join(SUB_DATA_DIR, 'mm_kinds.dat')
GOOD_MM_KIND_OUT = os.path.join(SUB_DATA_DIR, 'mm_kinds_good.dat')

QM_OUT_INI = os.path.join(SUB_DATA_DIR, 'psf_make_qmmm_no_exclude.ini')
GOOD_QM_OUT = os.path.join(SUB_DATA_DIR, 'amino_id_all_good.dat')
GOOD_VMD_QM_ATOMS_OUT = os.path.join(SUB_DATA_DIR, 'vmd_protein_atoms_qm_good.dat')

# To catch problems...
MOL_RENUM_REORDER_INI = os.path.join(SUB_DATA_DIR, 'psf_edit_renum_conflict.ini')
MISSING_MOL_DICT_INI = os.path.join(SUB_DATA_DIR, 'psf_edit_wrong_mol_dict.ini')
MISSING_ATOM_TYPE_INI = os.path.join(SUB_DATA_DIR, 'psf_edit_bad_atom_type.ini')
MISSING_RADIUS_INI = os.path.join(SUB_DATA_DIR, 'psf_qmmm_missing_radius.ini')
STRING_RESID_INI = os.path.join(SUB_DATA_DIR, 'psf_make_qm_string_resid.ini')


class TestPSFEditFailWell(unittest.TestCase):
    def testNoArgs(self):
        with capture_stderr(main, []) as output:
            self.assertTrue("Could not read file" in output)

    def testRenumReorderMol(self):
        test_input = ["-c", MOL_RENUM_REORDER_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("does not currently support both" in output)

    def testMissingMolDict(self):
        with capture_stderr(main, ["-c", MISSING_MOL_DICT_INI]) as output:
            self.assertTrue("No such file or directory" in output)

    def testMissingAtomType(self):
        with capture_stderr(main, ["-c", MISSING_ATOM_TYPE_INI]) as output:
            self.assertTrue("Did not find atom type 'XYZ' in the element dictionary" in output)

    def testStringResid(self):
        test_input = ["-c", STRING_RESID_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("expected only integers" in output)


class TestPSFEdit(unittest.TestCase):
    def testRenumMol(self):
        try:
            main(["-c", DEF_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT)

    def testRenumDictMol(self):
        try:
            main(["-c", MOL_DICT_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)

    def testPrintQMMM(self):
        try:
            test_input = ["-c", QMMM_OUT_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stdout(main, test_input) as output:
                self.assertTrue("Total charge from QM atoms: -1.0" in output)
            self.assertFalse(diff_lines(QMMM_OUT, GOOD_QMMM_OUT))
            self.assertFalse(diff_lines(MM_KIND_OUT, GOOD_MM_KIND_OUT))
            self.assertFalse(diff_lines(VMD_ATOMS_OUT, GOOD_VMD_ATOMS_OUT))
        finally:
            silent_remove(QMMM_OUT, disable=DISABLE_REMOVE)
            silent_remove(MM_KIND_OUT, disable=DISABLE_REMOVE)
            silent_remove(VMD_ATOMS_OUT, disable=DISABLE_REMOVE)

    def testPrintQMMMNoExclude(self):
        try:
            main(["-c", QM_OUT_INI])
            self.assertFalse(diff_lines(MM_KIND_OUT, GOOD_MM_KIND_OUT))
            self.assertFalse(diff_lines(QMMM_OUT, GOOD_QM_OUT))
            self.assertFalse(diff_lines(VMD_ATOMS_OUT, GOOD_VMD_QM_ATOMS_OUT))
        finally:
            silent_remove(MM_KIND_OUT, disable=DISABLE_REMOVE)
            silent_remove(QMMM_OUT, disable=DISABLE_REMOVE)
            silent_remove(VMD_ATOMS_OUT, disable=DISABLE_REMOVE)

    def testMissingRadius(self):
        # Tests both providing a dictionary and not having an available radius (still prints everything, just missing
        # one radius)
        try:
            test_input = ["-c", MISSING_RADIUS_INI]
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            with capture_stderr(main, test_input) as output:
                self.assertTrue("Did not find atom type 'XYZ' in the atom_type to radius dictionary" in output)
            self.assertFalse(diff_lines(QMMM_OUT, GOOD_QMMM_OUT))
            self.assertFalse(diff_lines(MM_KIND_OUT, GOOD_MM_KIND_OUT))
            self.assertFalse(diff_lines(VMD_ATOMS_OUT, GOOD_VMD_ATOMS_OUT))
        finally:
            silent_remove(QMMM_OUT, disable=DISABLE_REMOVE)
            silent_remove(MM_KIND_OUT, disable=DISABLE_REMOVE)
            silent_remove(VMD_ATOMS_OUT, disable=DISABLE_REMOVE)
