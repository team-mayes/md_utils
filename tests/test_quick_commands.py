# coding=utf-8

"""
Tests for add_head_tail.py.
"""
import unittest
import itertools

__author__ = 'hmayes'


def quick_print():
    """
    """
    # names = ["cl_pos_flow", "cl_neg_flow",]
    # names = ["h_pos_flow", "h_neg_flow",]
    names = ["joint_flow"]
    print("hello hello!!!")
    for prefix in ["", "bth_"]:
        for name in names:
            print("ErrorBars/T=4/L=4 {0}{1} Y,wave=({0}err_{1},{0}err_{1})".format(prefix, name))
    return True


class TestReadData(unittest.TestCase):
    def testReadMeta(self):
        self.assertTrue(quick_print())


class TestPlay(unittest.TestCase):
    def testJoinLists(self):
        letters = ['a', 'b', 'c', 'd', 'e', 'f']
        booleans = [1, 0, 1, 0, 0, 1]
        # numbers = [23, 20, 44, 32, 7, 12]
        decimals = [0.1, 0.7, 0.4, 0.4, 0.5]
        new_list = list(itertools.chain(letters, booleans, decimals))
        print(new_list)
        list1 = [["hello_key", "hello_val"],
                 ["a", 5],
                 ["b", 2]]
        list2 = [["there_key", "there_val"],
                 ["c", 1],
                 ["d", 6],
                 ["e", 2]]
        # print list(itertools.imap(sum, numbers, decimals))
        # new_list = list(itertools.imap(None, list1[:], list2[:]))
        new_list = []
        len1 = len(list1)
        len2 = len(list2)
        width1 = len(list1[0])
        width2 = len(list2[0])
        another_list = [""] * 5
        print(another_list)
        for row in range(min(len1, len2)):
            new_list.append(list1[row] + list2[row])
        for row in range(len2, len1):
            new_list.append(list1[row] + [""] * width2)
        for row in range(len1, len2):
            new_list.append([""] * width1 + list2[row])
        for row in new_list:
            print(row)
        self.assertTrue(True)
