import unittest
import os
from md_utils.FEP_edit import main
from md_utils.md_common import diff_lines, capture_stderr, silent_remove, capture_stdout
import logging

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'xadams'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'FEP_edit')

DEF_INI = os.path.join(SUB_DATA_DIR, 'FEP_edit.ini')
# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(SUB_DATA_DIR, 'short_new.fepout')
GOOD_FEP_OUT = os.path.join(SUB_DATA_DIR, 'short_good.fepout')

# For catching errors
NO_FEP_INI = os.path.join(SUB_DATA_DIR, 'FEP_edit_no_file.ini')
UNEXPECTED_KEY_INI = os.path.join(SUB_DATA_DIR, 'FEP_edit_wrong_key.ini')


class TestFEPEditMain(unittest.TestCase):
    # Testing normal function; can use inputs here as examples
    def testShiftTimestep(self):
        try:
            main(["-c", DEF_INI])
            self.assertFalse(diff_lines(DEF_OUT, GOOD_FEP_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)


class TestFEPEditCatchImperfectInput(unittest.TestCase):
    # Testing for elegant failure and hopefully helpful error messages
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoIni(self):
        # main(["-c", "ghost.ini"])
        with capture_stderr(main, ["-c", "ghost.ini"]) as output:
            self.assertTrue("Could not read file" in output)

    def testMissingReqKey(self):
        # main(["-c", NO_PDB_INI])
        with capture_stderr(main, ["-c", NO_FEP_INI]) as output:
            self.assertTrue("Missing config val" in output)

    def testUnexpectedKey(self):
        # main(["-c", UNEXPECTED_KEY_INI])
        with capture_stderr(main, ["-c", UNEXPECTED_KEY_INI]) as output:
            self.assertTrue("Unexpected key" in output)
