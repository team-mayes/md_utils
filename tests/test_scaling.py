# coding=utf-8

"""
"""

import unittest
import logging
import os
from md_utils.md_common import silent_remove, capture_stderr, capture_stdout, diff_lines
from md_utils.scaling import main

__author__ = 'xadams and cluyet'

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SCALING_DIR = os.path.join(DATA_DIR, 'scaling')
BASENAME = os.path.join(SCALING_DIR, "scaling")
CONF_FILE = os.path.join("md_utils/skel/tpl/template.inp")
GOOD_RESUBMIT = os.path.join(SCALING_DIR, "good_scaling_resubmit.job")
GOOD_ANALYSIS = os.path.join(SCALING_DIR, "good_scaling_analysis.job")
PNG_OUT = os.path.join(SCALING_DIR, "scaling.png")
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
            with capture_stdout(main, test_input) as output:
                self.assertTrue("subprocess.call" in output)
                for num in PROC_LIST:
                    self.assertTrue(os.path.isfile(BASENAME + '_' + num + '.job'))
                    self.assertTrue(os.path.isfile(BASENAME + '_' + num + '.conf'))
        finally:
            for num in PROC_LIST:
                silent_remove(BASENAME + '_' + num + '.job', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_' + num + '.conf', disable=DISABLE_REMOVE)

    def testJobOutput(self):
        test_input = ['-b', BASENAME, '-c', CONF_FILE, '-d']
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue("subprocess.call" in output)
        finally:
            for num in PROC_LIST:
                silent_remove(BASENAME + '_' + num + '.job', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_' + num + '.conf', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_analysis.job', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_resubmit.job', disable=DISABLE_REMOVE)

    def testAnalysisOutput(self):
        test_input = ['-b', BASENAME, '-c', CONF_FILE, '-d', '-p', "1 2", '--nnodes', "1"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(BASENAME + '_analysis.job', GOOD_ANALYSIS))
            self.assertFalse(diff_lines(BASENAME + '_resubmit.job', GOOD_RESUBMIT))
        finally:
            silent_remove(BASENAME + '_1.job', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_1.conf', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_2.job', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_2.conf', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_analysis.job', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_resubmit.job', disable=DISABLE_REMOVE)

    def testPlotting(self):
        test_input = ['-b', BASENAME, '-c', CONF_FILE, '-d', '-p', "1 2 4 8 12", '--nnodes', "1", "--plot"]
        try:
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_OUT))
        finally:
            silent_remove(PNG_OUT, silent_remove(PNG_OUT))
