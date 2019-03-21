# coding=utf-8

"""
"""

import unittest
import logging
import os
from md_utils.md_common import silent_remove, capture_stderr, capture_stdout, diff_lines
from md_utils.scaling import main

__author__ = 'xadams'

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SCALING_DIR = os.path.join(DATA_DIR, 'scaling')
BASENAME = os.path.join(SCALING_DIR, "scaling")
CONF_FILE = os.path.join(SCALING_DIR, "template.inp")

class TestMainFailWell(unittest.TestCase):
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testFileNames(self):
        test_input = ['-n', BASENAME, '-c', CONF_FILE, '-d', '-p', "1", "2", "4"]
        main(test_input)


class TestMain(unittest.TestCase):
    def testReadDistances(self):
        test_input = [DIST_FILE, "-n", NAME, "--outdir", PCA_DIR]
        try:
            silent_remove(PNG_2D_FILE)
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_2D_FILE))
        finally:
            silent_remove(PNG_2D_FILE, disable=DISABLE_REMOVE)

