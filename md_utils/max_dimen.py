#!/usr/bin/env python
"""
Given a file with an xyz vector (space separated, no other data), return the maximum x, y, and z coordinates, plus the
values after a buffer distance is added
"""

from __future__ import print_function

import numpy as np
from md_utils.md_common import InvalidDataError, warning
import sys
import argparse

__author__ = 'hmayes'


# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3

# Constants #

# Defaults
DEF_DIMEN_FILE = 'qm_box_sizes.txt'


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in space-separated xyz dimensions and returns the largest value'
                                                 'in each dimension.')
    parser.add_argument("-f", "--file", help="The location of the file with the dimensions with one line per vector, space-separated.",
                        default=DEF_DIMEN_FILE)
    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except KeyError as e:
        warning("Input data missing:", e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def process_file(data_file):
    dim_vectors = np.loadtxt(data_file,dtype=np.float64)
    max_vector =  dim_vectors.max(axis=0)
    print("Maximum value in each dimension: {}".format(max_vector))
    print("With 6 A buffer: {}".format(max_vector+6))
    return


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    try:
        process_file(args.file)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
