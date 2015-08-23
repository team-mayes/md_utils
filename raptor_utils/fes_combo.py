from __future__ import print_function
from raptor_utils.common import warning

__author__ = 'cmayes'

# !/usr/bin/env python

"""
Module docstring.
"""

import argparse
import os
import sys

# Defaults #

DEF_FILE_PAT = 'fes*.out'




# CLI Processing #

def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Combines one or more FES files into a single file '
                                                 'where each line has a timestep value unique to the '
                                                 'combined file.  Files with higher initial timestep '
                                                 'values take precedence.')
    parser.add_argument("-d", "--base_dir", help="The starting point for a file search "
                                                 "(defaults to current directory)",
                        default=os.getcwd())
    parser.add_argument('-p', "--pattern", help="The file pattern to search for.",
                        default=DEF_FILE_PAT)
    args = None
    try:
        args = parser.parse_args(argv)
    except IOError, e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, 2

    return args, 0


def main(argv=None):
    args, ret = parse_cmdline(argv)
    if ret != 0:
        return ret
    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
