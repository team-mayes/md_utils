# !/usr/bin/env python
# coding=utf-8

"""
Splits WHAM files and directories into 2-`n` partitions based on the number of
steps specified.
"""

from __future__ import print_function, division
import logging

from md_utils.common import find_files_by_dir

__author__ = 'cmayes'


import argparse
import os
import sys

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wham_split')

# Defaults #

DEF_FILE_PAT = 'meta.00'
DEF_STEPS_NUM = 12

# Logic #





# CLI Processing #


def parse_cmdline(argv=None):
    """
    Returns the parsed argument list and return code.
    :param argv: A list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Block averages input data for WHAM')
    parser.add_argument("-d", "--base_dir", help="The starting point for a meta file search "
                                                 "(defaults to current directory)",
                        default=os.getcwd())
    parser.add_argument('-p', "--pattern", help="The meta file pattern to search for "
                                                "(defaults to '{}')".format(DEF_FILE_PAT),
                        default=DEF_FILE_PAT)
    parser.add_argument('-s', "--steps", help="The number of averaging steps to take "
                                              "(defaults to '{}')".format(DEF_STEPS_NUM),
                        type=int, default=DEF_STEPS_NUM)
    parser.add_argument('-o', "--overwrite", help='Overwrite existing locations',
                        action='store_true')
    args = parser.parse_args(argv)

    return args, 0


def main(argv=None):
    """
    Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != 0:
        return ret

    for meta_dir, meta_files in find_files_by_dir(args.base_dir, args.pattern).items():
        for meta_file in meta_files:
            pass
            #block_average(os.path.join(meta_dir, meta_file), args.steps, args.overwrite)

    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
