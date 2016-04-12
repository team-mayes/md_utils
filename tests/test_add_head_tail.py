# coding=utf-8

"""
Tests for add_head_tail.py.
"""
import os
import unittest

from md_utils import add_head_tail
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


class TestAddHeadTail(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(add_head_tail.main, []) as output:
            self.assertTrue("usage:" in output)
        with capture_stderr(add_head_tail.main, []) as output:
            self.assertTrue("too few arguments" in output)

    def testAddHead(self):
        try:
            add_head_tail.main([INPUT_PATH, "-b", "../"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, PREFIX_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testAddTail(self):
        try:
            add_head_tail.main([INPUT_PATH, "-e", ".txt"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, SUFFIX_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testAddBoth(self):
        try:
            add_head_tail.main([INPUT_PATH, "-b", "../", "-e", ".txt"])
            self.assertFalse(diff_lines(DEF_OUT_PATH, BOTH_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)

    def testSpecifyOutfile(self):
        try:
            add_head_tail.main([INPUT_PATH, "-b", "../", "-e", ".txt", "-n", NEW_OUT_PATH])
            self.assertFalse(diff_lines(NEW_OUT_PATH, BOTH_OUT_PATH))
        finally:
            silent_remove(NEW_OUT_PATH)

    def testAddNothing(self):
        try:
            with capture_stderr(add_head_tail.main, [INPUT_PATH]) as output:
                self.assertTrue("Return file will be the same as the input" in output)
            self.assertFalse(diff_lines(INPUT_PATH, DEF_OUT_PATH))
        finally:
            silent_remove(DEF_OUT_PATH)
