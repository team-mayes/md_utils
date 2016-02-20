#!/usr/bin/env python
"""
Adds a string to the beginning and end of a file.
"""

from __future__ import print_function

import numpy as np
import logging
from md_utils.md_common import list_to_file, InvalidDataError, seq_list_to_file, create_out_suf_fname, warning, create_out_fname
import sys
import argparse

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('max_dimen')
logging.basicConfig(filename='max_dimen.log', filemode='w', level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)



# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3

# Constants #

# Defaults
DEF_BEGIN_STR = ''
DEF_END_STR = ''
DEF_NEW_FNAME = None



def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in a file and adds a begging and/or end to each line.')
    parser.add_argument("-f", "--file", help="The location of the file to be ammended.")
    parser.add_argument("-b", "--begin", help="String to add to the beginning of a line.",
                        default=DEF_BEGIN_STR)
    parser.add_argument("-e", "--end", help="String to add to the end of a line.",
                        default=DEF_END_STR)
    parser.add_argument("-n", "--new_name", help="Name of amended file.",
                        default=DEF_NEW_FNAME)
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


def process_file(f_name, b_str, e_str, new_f_name):

    if new_f_name is None:
        new_f_name = create_out_suf_fname(f_name, '_ammend')

    with open(new_f_name, 'w') as myfile:
        with open(f_name) as f:
            for line in f.readlines():
                # string2 = string1.strip('\n')
                line = line.strip()
                myfile.write(b_str + line + e_str + "\n")

    # with open(f_name) as myfile:
    #     for line in list_val:
    #         myfile.write(line + "\n")


    return



def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    # TODO: did not show the expected behavior when I didn't have a required cfg in the ini file
    if ret != GOOD_RET:
        return ret

    try:
        process_file(args.file, args.begin, args.end, args.new_name)
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
