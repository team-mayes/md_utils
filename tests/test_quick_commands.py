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
    names = ["1", "300"]
    for prefix in ["cl_avg_bound", "pka_148", "pka_203"]:
        for name in names:
            print("ReplaceWave trace= Cl_rate_cl{0}, {1}_{0}\n"
                  "ErrorBars {1}_{0} Y,wave=(err_{1}_{0},err_{1}_{0})".format(name, prefix))
    return True


class TestReadData(unittest.TestCase):
    def testReadMeta(self):
        self.assertTrue(quick_print())


def print_bin(int_list):
    print("{} is:".format(str(int_list)))
    for int_val in int_list:
        if int_val == int_list[-1]:
            print("{:05b}".format(int_val))
        else:
            print("{:05b} to".format(int_val))
    return True


class PrintBin(unittest.TestCase):
    def testPrintBin(self):
        self.assertTrue(print_bin([6, 14, 22, 18, 2, 6]))


class TestPlay(unittest.TestCase):
    def testJoinLists(self):
        letters = ['a', 'b', 'c', 'd', 'e', 'f']
        booleans = [1, 0, 1, 0, 0, 1]
        # numbers = [23, 20, 44, 32, 7, 12]
        decimals = [0.1, 0.7, 0.4, 0.4, 0.5]
        new_list = list(itertools.chain(letters, booleans, decimals))
        print(new_list)
        list1 = [["hey_key", "hey_val"],
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
