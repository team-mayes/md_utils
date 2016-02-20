# coding=utf-8

"""
Tests for add_head_tail.py.
"""

import unittest

from md_utils import add_head_tail
from md_utils.md_common import capture_stdout, capture_stderr, diff_lines, silent_remove


__author__ = 'hmayes'


class TestAddHeadTail(unittest.TestCase):
    def testNoArgs(self):
        with capture_stdout(add_head_tail.main,[]) as output:
            self.assertTrue("usage:" in output)
        with capture_stderr(add_head_tail.main,[]) as output:
            self.assertTrue("too few arguments" in output)
    def testAddHead(self):
        try:
            add_head_tail.main(["add_head_tail_input.txt", "-b", "../"])
            self.assertFalse(diff_lines("add_head_tail_input_amend.txt", "add_head_tail_prefixed.txt"))
        finally:
            silent_remove("add_head_tail_input_amend.txt")
    def testAddTail(self):
        try:
            add_head_tail.main(["add_head_tail_input.txt", "-e", ".txt"])
            self.assertFalse(diff_lines("add_head_tail_input_amend.txt", "add_head_tail_suffix.txt"))
        finally:
            silent_remove("add_head_tail_input_amend.txt")
    def testAddBoth(self):
        try:
            add_head_tail.main(["add_head_tail_input.txt", "-b", "../", "-e", ".txt"])
            self.assertFalse(diff_lines("add_head_tail_input_amend.txt", "add_head_tail_prefix_suffix.txt"))
        finally:
            print("hello")
            # silent_remove("add_head_tail_input_amend.txt")
    def testAddNothing(self):
        try:
            with capture_stderr(add_head_tail.main,["add_head_tail_input.txt"]) as output:
                self.assertTrue("Return file will be the same as the input" in output)
            self.assertFalse(diff_lines("add_head_tail_input.txt", "add_head_tail_input_amend.txt"))
        finally:
            silent_remove("add_head_tail_input_amend.txt")
