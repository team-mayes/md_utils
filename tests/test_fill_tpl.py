# coding=utf-8

"""
Tests for an md_utils program
"""
import os
import unittest
from md_utils.fill_tpl import main, FILLED_TPL_FNAME
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove
import logging

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'


DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'fill_tpl')

PAR_INI = os.path.join(SUB_DATA_DIR, 'make_par.ini')
PAR_NO_NEW_FILE_NAME_INI = os.path.join(SUB_DATA_DIR, 'no_new_fname.ini')
PAR_FNAME = 'evb_test.par'
PAR_OUT = os.path.join(SUB_DATA_DIR, PAR_FNAME)
GOOD_PAR_OUT = os.path.join(SUB_DATA_DIR, 'evb_test_good.par')

MISSING_DEF_TPL_INI = os.path.join(SUB_DATA_DIR, 'missing_def_tpl.ini')
MISSING_TPL_INI = os.path.join(SUB_DATA_DIR, 'missing_tpl.ini')
MISSING_TPL_KEY_INI = os.path.join(SUB_DATA_DIR, 'missing_tpl_key.ini')
TPL_KEY_IN_MAIN_INI = os.path.join(SUB_DATA_DIR, 'tpl_key_in_main.ini')


class TestMakeParFailWell(unittest.TestCase):
    # These tests only check for (hopefully) helpful messages
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testMissingDefaultTpl(self):
        test_input = ["-c", MISSING_DEF_TPL_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("default template file" in output)

    def testMissingTpl(self):
        test_input = ["-c", MISSING_TPL_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("template file specified" in output)

    def testMissingFilledTplName(self):
        # new file name not specified by either config file or command line
        test_input = ["-c", PAR_NO_NEW_FILE_NAME_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue(FILLED_TPL_FNAME in output)

    def testTplKeyInMain(self):
        # aim for a helpful message if the template key is in main
        test_input = ["-c", TPL_KEY_IN_MAIN_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('Unexpected key' in output)

    def testMissingTplKey(self):
        # make sure it gracefully fails when a template key is missing
        test_input = ["-c", MISSING_TPL_KEY_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue('required for template file' in output)


class TestMain(unittest.TestCase):
    def testMakePar(self):
        try:
            silent_remove(PAR_OUT)
            main(["-c", PAR_INI])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)

    def testMakeParCommandLine(self):
        try:
            silent_remove(PAR_OUT)
            main(["-c", PAR_NO_NEW_FILE_NAME_INI, "-f", PAR_FNAME])
            self.assertFalse(diff_lines(PAR_OUT, GOOD_PAR_OUT))
        finally:
            silent_remove(PAR_OUT, disable=DISABLE_REMOVE)
