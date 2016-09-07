# coding=utf-8

"""
Tests for add_to_each_line.py.
"""
import os
import unittest

from md_utils.add_to_each_line import main
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
HEAD_TAIL_DATA_DIR = os.path.join(DATA_DIR, 'small_tests')

INPUT_PATH = os.path.join(HEAD_TAIL_DATA_DIR, 'add_head_tail_input.txt')
# noinspection PyUnresolvedReferences

DEF_OUT_PATH = os.path.join(HEAD_TAIL_DATA_DIR, 'add_head_tail_input_amend.txt')
# noinspection PyUnresolvedReferences
NEW_OUT_PATH = os.path.join(HEAD_TAIL_DATA_DIR, 'add_head_tail_input_new.txt')
PREFIX_OUT_PATH = os.path.join(HEAD_TAIL_DATA_DIR, 'add_head_tail_prefixed.txt')
SUFFIX_OUT_PATH = os.path.join(HEAD_TAIL_DATA_DIR, 'add_head_tail_suffix.txt')
BOTH_OUT_PATH = os.path.join(HEAD_TAIL_DATA_DIR, 'add_head_tail_prefix_suffix.txt')


class TestAddHeadTailNoOutput(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(main, []) as output:
            self.assertTrue("usage:" in output)
        with capture_stderr(main, []) as output:
            self.assertTrue("too few arguments" in output)

    def testMissingFile(self):
        # main(["ghost.txt", "-e", ".txt"])
        with capture_stderr(main, ["ghost.txt", "-e", ".txt"]) as output:
            self.assertTrue("No such file or directory" in output)


class TestAddHeadTail(unittest.TestCase):
    # These will show example usage
    def testAddNothing(self):
        # this first test does not really doing anything, and warns the user
        try:
            with capture_stderr(main, [INPUT_PATH]) as output:
                self.assertTrue("Return file will be the same as the input" in output)
            self.assertFalse(diff_lines(INPUT_PATH, DEF_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testAddHead(self):
        try:
            main([INPUT_PATH, "-b", "../"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, PREFIX_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testAddTail(self):
        try:
            main([INPUT_PATH, "-e", ".txt"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, SUFFIX_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testAddBoth(self):
        try:
            main([INPUT_PATH, "-b", "../", "-e", ".txt"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, BOTH_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testSpecifyOutfile(self):
        try:
            main([INPUT_PATH, "-b", "../", "-e", ".txt", "-n", NEW_OUT_PATH])
            self.assertFalse(diff_lines(NEW_OUT_PATH, BOTH_OUT_PATH))
        finally:
            silent_remove(NEW_OUT_PATH)

