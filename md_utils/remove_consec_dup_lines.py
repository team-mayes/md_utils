#!/usr/bin/env python
"""
Removes consecutive duplicate lines
"""

from __future__ import print_function

import ConfigParser
import logging
from md_utils.md_common import list_to_file, InvalidDataError, seq_list_to_file, create_out_suf_fname, warning
import sys
import argparse

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('remove_consec_dup_lines')
logging.basicConfig(filename='remove_consec_dup_lines.log', filemode='w', level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)

# Constants #



# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3

def to_int_list(raw_val):
    return_vals = []
    for val in raw_val.split(','):
        return_vals.append(int(val.strip()))
    return return_vals


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Compares sequential lines of files. If two consequtive lines are '
                                                 'equal, keeps only the first.')
    parser.add_argument("-f", "--src_file", help="The location of the file to be processed."
                                               "format. See the example file /test/test_data/evbd2d/compare_data.ini. "
                                               "The default file name is compare_data.ini, located in the "
                                               "base directory where the program as run.")
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


def print_data(head, data, tail, f_name):
    list_to_file(head, f_name)
    seq_list_to_file(data, f_name, mode='a')
    list_to_file(tail, f_name, mode='a')
    return


def proc_file(file_name):
    with open(file_name) as d:
        nodups_lines = ['']
        for line in d.readlines():
            line = line.strip()
            if len(line) == 0:
                continue
            elif line == nodups_lines[-1]:
                continue
            else:
                nodups_lines.append(line)
    print('Completed reading',file_name)
    print('')
    f_out_name = create_out_suf_fname(file_name, '_nodups')
    list_to_file(nodups_lines[1:], f_out_name)
    return


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    # if args.src_file is not None:
    try:
        proc_file(args.src_file)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data template:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
