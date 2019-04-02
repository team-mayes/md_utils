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
CONF_FILE = os.path.join(SCALING_DIR, "template.inp")
GOOD_PBS_RESUBMIT = os.path.join(SCALING_DIR, "good_scaling_resubmit.pbs")
GOOD_PBS_ANALYSIS = os.path.join(SCALING_DIR, "good_scaling_analysis.pbs")
GOOD_SLURM_ANALYSIS = os.path.join(SCALING_DIR, "good_scaling_analysis.job")
GOOD_SLURM_RESUBMIT = os.path.join(SCALING_DIR, "good_scaling_resubmit.job")
GOOD_CONF = os.path.join(SCALING_DIR, "good_scaling_1.conf")
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

    def testNoConfig(self):
        test_input = []
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("No config" in output)

    def testAmber(self):
        test_input = ['-b', BASENAME, '-c', CONF_FILE, '--software', "amber"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("xadams" in output)

    # TODO:Test for skip message when logfile exists


class TestMain(unittest.TestCase):
    def testFileNamesPBS(self):
        test_input = ['-b', BASENAME, '-c', CONF_FILE, '-d', '-p', PROC_STRING, '--nnodes', NODE_STRING]
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue("subprocess.call" in output)
                for num in PROC_LIST:
                    self.assertTrue(os.path.isfile(BASENAME + '_' + num + '.pbs'))
                    self.assertTrue(os.path.isfile(BASENAME + '_' + num + '.conf'))
        finally:
            for num in PROC_LIST:
                silent_remove(BASENAME + '_' + num + '.pbs', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_' + num + '.conf', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_analysis.pbs', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_resubmit.pbs', disable=DISABLE_REMOVE)

    def testJobOutputPBS(self):
        test_input = ['-b', BASENAME, '-c', CONF_FILE, '-d', '--nnodes', "1 2"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue("subprocess.call" in output)
                self.assertFalse(diff_lines(BASENAME + '_1.conf', GOOD_CONF))
                # TODO: Add test for pbs file as well
        finally:
            for num in PROC_LIST:
                silent_remove(BASENAME + '_' + num + '.pbs', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_' + num + '.conf', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_analysis.pbs', disable=DISABLE_REMOVE)
                silent_remove(BASENAME + '_resubmit.pbs', disable=DISABLE_REMOVE)

    def testAnalysisOutputPBS(self):
        test_input = ['-b', BASENAME, '-c', CONF_FILE, '-d', '-p', "1 2"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(BASENAME + '_analysis.pbs', GOOD_PBS_ANALYSIS))
            self.assertFalse(diff_lines(BASENAME + '_resubmit.pbs', GOOD_PBS_RESUBMIT))
        finally:
            silent_remove(BASENAME + '_1.pbs', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_1.conf', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_2.pbs', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_2.conf', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_analysis.pbs', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_resubmit.pbs', disable=DISABLE_REMOVE)

    # This test combines all previous PBS scripts, which are best used for diagnostics
    def testBridges(self):
        test_input = ['-b', BASENAME, '-c', CONF_FILE, '-d', '-p', "1 28", '--cluster', 'bridges']
        try:
            with capture_stdout(main, test_input) as output:
                self.assertTrue('sbatch' in output)
            self.assertFalse(diff_lines(BASENAME + '_analysis.job', GOOD_SLURM_ANALYSIS))
            self.assertFalse(diff_lines(BASENAME + '_resubmit.job', GOOD_SLURM_RESUBMIT))
            self.assertFalse(diff_lines(BASENAME + '_1.conf', GOOD_CONF))
        finally:
            silent_remove(BASENAME + '_1.job', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_1.conf', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_28.job', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_28.conf', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_analysis.job', disable=DISABLE_REMOVE)
            silent_remove(BASENAME + '_resubmit.job', disable=DISABLE_REMOVE)

    def testPlotting(self):
        test_input = ['-b', BASENAME, '-c', CONF_FILE, '-d', '-p', "1 2 4 8 12", "--plot"]
        try:
            main(test_input)
            self.assertTrue(os.path.isfile(PNG_OUT))
        finally:
            silent_remove(PNG_OUT, disable=DISABLE_REMOVE)
