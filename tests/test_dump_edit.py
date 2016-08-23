import unittest
import os
from md_utils.dump_edit import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
import logging

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'dump_edit')

# Input files #

DEF_INI = os.path.join(SUB_DATA_DIR, 'dump_edit.ini')
REPRODUCE_INI = os.path.join(SUB_DATA_DIR, 'dump_edit_reproduce.ini')
SHORTER_INI = os.path.join(SUB_DATA_DIR, 'dump_shorter.ini')
SKIP_INI = os.path.join(SUB_DATA_DIR, 'dump_every_2every3.ini')
REORDER_INI = os.path.join(SUB_DATA_DIR, 'dump_edit.ini')
REORDER_RENUM_INI = os.path.join(SUB_DATA_DIR, 'dump_renum_mol.ini')
RETYPE_INI = os.path.join(SUB_DATA_DIR, 'dump_renum_mol_retype.ini')
MISSING_DICT_INI = os.path.join(SUB_DATA_DIR, 'dump_missing_dict_file.ini')
MISSING_DUMP_INI = os.path.join(SUB_DATA_DIR, 'dump_missing_dump_file.ini')

# Output files

# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(SUB_DATA_DIR, '0.625_20c_short_reorder.dump')
DUMP_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_short.dump')
SHORT_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_4steps.dump')
SKIP_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_2every3.dump')
GOOD_ATOM_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_short_reorder_good.dump')
GOOD_RENUM_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_short_reorder_renum_good.dump')
GOOD_OUT_FILE = os.path.join(SUB_DATA_DIR, '0.625_20c_reord_renum_retype_good.dump')


class TestDumpEditFailWell(unittest.TestCase):
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testMissingDictFile(self):
        with capture_stderr(main, ["-c", MISSING_DICT_INI]) as output:
            self.assertTrue("Problems reading file" in output)

    def testMissingDumpFile(self):
        with capture_stderr(main, ["-c", MISSING_DUMP_INI]) as output:
            self.assertTrue("No such file or directory" in output)


class TestDumpEdit(unittest.TestCase):
    def testNoArgs(self):
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Could not read file" in output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testReproduceDump(self):
        try:
            main(["-c", REPRODUCE_INI])
            self.assertFalse(diff_lines(DEF_OUT, DUMP_FILE))
        finally:
            silent_remove(DEF_OUT)

    def testFewerSteps(self):
        try:
            main(["-c", SHORTER_INI])
            self.assertFalse(diff_lines(DEF_OUT, SHORT_OUT_FILE))
        finally:
            silent_remove(DEF_OUT)

    def testSkipSteps(self):
        try:
            main(["-c", SKIP_INI])
            self.assertFalse(diff_lines(DEF_OUT, SKIP_OUT_FILE))
        finally:
            silent_remove(DEF_OUT)

    def testReorderAtoms(self):
        try:
            main(["-c", REORDER_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_ATOM_OUT_FILE))
        finally:
            silent_remove(DEF_OUT)

    def testReorderAtomRenumMol(self):
        try:
            main(["-c", REORDER_RENUM_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_RENUM_OUT_FILE))
        finally:
            silent_remove(DEF_OUT)

    def testRetypeAtom(self):
        try:
            main(["-c", RETYPE_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT_FILE))
        finally:
            silent_remove(DEF_OUT)
