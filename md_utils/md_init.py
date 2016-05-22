#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initializes a location for running md utilities.  The contents
of the "skel" subdirectory are copied into the target directory.
This currently includes a tpl directory.
"""
import argparse
import logging
import sys

import os

from md_utils import md_common

logger = logging.getLogger(__name__)

DEF_SKEL_LOC = os.path.join(os.path.dirname(__file__), 'skel')

# Logic #

def copy_skel(src, dest):
    """Copies the contents of src to dest."""
    md_common.copytree(src, dest)


# CLI Processing #


def parse_cmdline(argv=None):
    """
    Returns the parsed argument list and return code.
    :param argv: A list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Copy initial template files '
                                                 'into the target location.')

    parser.add_argument('-s', '--skel_dir', default=DEF_SKEL_LOC,
                        help="Specify skel directory.", metavar="SKEL")
    parser.add_argument("-t", "--tgt_dir", help="The target directory for the copy "
                                                "(defaults to current directory)",
                        default=os.getcwd())
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

    copy_skel(args.skel_dir, args.tgt_dir)

    return 0  # success

if __name__ == '__main__':
    status = main()
    sys.exit(status)
