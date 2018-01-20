# !/usr/bin/env python
# coding=utf-8

"""
Renames files which have spaces in their names
"""
from __future__ import print_function

import argparse
import logging
import os
import sys

import re

from md_utils.md_common import (GOOD_RET, INPUT_ERROR, warning, create_out_fname)

__author__ = 'hmayes'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants #

# Defaults #

# want any files with a space in the name
DEF_FILE_PAT = ' '
DEF_NEW_FILE_PAT = ''


# Logic #


# CLI Processing #


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    :param argv: is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Renames files which contain (by default) a space in the name to '
                                                 'the same filename without the space. The pattern can be changed '
                                                 'to replace a different character or pattern')
    parser.add_argument("-d", "--base_dir", help="The starting point for a file search "
                                                 "(defaults to current directory)",
                        default=os.getcwd())
    parser.add_argument('-p', "--pattern", help="The file pattern to search for "
                                                "(defaults to '{}')".format(DEF_FILE_PAT),
                        default=DEF_FILE_PAT)

    parser.add_argument('-n', "--new_pattern", help="The new pattern to use in changing the file name "
                                                    "(defaults to '{}')".format(DEF_NEW_FILE_PAT),
                        default=DEF_NEW_FILE_PAT)

    parser.add_argument('-b', "--begin", help="String to add to the beginning of the file name. "
                                              "By default, nothing is added.",
                        default="")

    parser.add_argument('-s', "--suffix", help="String to add to the end of the file name, before the extension. "
                                               "By default, nothing is added.",
                        default="")

    parser.add_argument('-e', "--ext", help="New extension for file name (replacement or add if new). By default, "
                                            "no change is made to the extension.",
                        default=None)

    args = None
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        if hasattr(e, 'code') and e.code == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def rename_files_by_dir(tgt_dir, pattern, new_pattern, prefix, suffix, ext):
    """
    Alternate filename matching
    :param tgt_dir: base file in which to search
    :param pattern: string to replaced
    :param new_pattern: string to replace the pattern string
    :param prefix: String to add to the beginning of the file name
    :param suffix: String to add to the end of the file name, before the extension.
    :param ext: New extension for file name (replacement or add if new)
    :return: an integer representing the number of files renamed
    """
    num_files_renamed = 0
    pat_match = re.compile(r".*" + re.escape(pattern) + r".*")
    for root, dirs, files in os.walk(tgt_dir):
        for fname in files:
            if pat_match.match(fname):
                old_name = os.path.abspath(os.path.join(root, fname))
                new_name = create_out_fname(fname.replace(pattern, new_pattern), prefix=prefix, suffix=suffix,
                                            base_dir=root, ext=ext)
                os.rename(old_name, new_name)
                num_files_renamed += 1
    return num_files_renamed


def main(argv=None):
    """ Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    num_renamed_files = rename_files_by_dir(args.base_dir, args.pattern, args.new_pattern,
                                            args.begin, args.suffix, args.ext)
    print("Found and renamed {} files".format(num_renamed_files))
    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
