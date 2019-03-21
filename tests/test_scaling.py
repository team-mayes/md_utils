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
CONF_FILE = os.path.join("md_utils/skel/tpl/template.inp")
PROC_LIST = ["1", "2", "4", "8", "12"]
PROC_STRING = ' '.join(map(str, PROC_LIST))
NODE_LIST = ["1", "2"]
NODE_STRING = ' '.join(map(str, NODE_LIST))
for n in NODE_LIST:
    if int(n) > 1:
        print(n, PROC_LIST[-1])
        PROC_LIST.append(str(int(n) * int(PROC_LIST[-1])))


class TestMainFailWell(unittest.TestCase):
    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)


class TestMain(unittest.TestCase):
    def testFileNames(self):
        test_input = ['-b', BASENAME, '-c', CONF_FILE, '-d', '-p', PROC_STRING, '--nnodes', NODE_STRING]
        try:
            main(test_input)
            for num in PROC_LIST:
                self.assertTrue(os.path.isfile(BASENAME + '_' + num + '.pbs'))
                self.assertTrue(os.path.isfile(BASENAME + '_' + num + '.conf'))
        finally:
            for num in PROC_LIST:
                silent_remove(BASENAME + '_' + num + '.pbs', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_' + num + '.conf', disable=DISABLE_REMOVE)
    # TODO: Addd a test that actually checks for content
