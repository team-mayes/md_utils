import unittest
import os
import logging
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
from md_utils.vmd_index_proc import DEF_CFG_FILE, main

__author__ = 'hmayes'

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

# Directories #

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'vmd_index_proc')

# Input files #

DEF_INPUT = os.path.join(SUB_DATA_DIR, "IG_indices.txt")
DEF_INI = os.path.join(SUB_DATA_DIR, DEF_CFG_FILE)
TYPO_INI = os.path.join(SUB_DATA_DIR, "vmd_index_proc_typo.ini")
PARSE_ERROR_INI = os.path.join(SUB_DATA_DIR, "vmd_index_proc_parse_error.ini")

# Output files #

# noinspection PyUnresolvedReferences
DEF_OUT = os.path.join(SUB_DATA_DIR, "vmd_index_proc.txt")
GOOD_OUT = os.path.join(SUB_DATA_DIR, "IG_indices_good.txt")


class TestVMDPROCFailWell(unittest.TestCase):
    def testNoArgs(self):
        with capture_stderr(main, []) as output:
            self.assertTrue("Could not read file {}".format(DEF_CFG_FILE) in output)

    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoSuchFile(self):
        test_input = ["-f", "ghost.csv", "-c", DEF_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Problems reading file" in output)

    def testWrongFileToFilter(self):
        # If put a configuration file as the file to read, fail well
        test_input = ["-f", DEF_INI, "-c", DEF_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("could not convert string" in output)

    def testInvalidKey(self):
        test_input = ["-f", DEF_INPUT, "-c", TYPO_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("Unexpected key" in output)

    def testParseError(self):
        # This input has a line without equals), resulting in a parsing error we will catch
        test_input = ["-f", DEF_INPUT, "-c", PARSE_ERROR_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("parsing errors" in output)
            self.assertTrue("'col2" in output)


class TestVMDPROC(unittest.TestCase):
    def testDefInp(self):
        test_input = ["-c", DEF_INI, "-f", DEF_INPUT]
        try:
            main(test_input)
            self.assertFalse(diff_lines(DEF_OUT, GOOD_OUT))
        finally:
            silent_remove(DEF_OUT, disable=DISABLE_REMOVE)
