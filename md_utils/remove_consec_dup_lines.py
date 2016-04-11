#!/usr/bin/env python
"""
Removes consecutive duplicate lines
"""

from __future__ import print_function
import sys
import argparse

from md_utils.md_common import list_to_file, InvalidDataError, create_out_fname, warning

__author__ = 'hmayes'


# Constants #

# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Compares sequential lines of files. If two consecutive lines are '
                                                 'equal, keeps only the first.')
    parser.add_argument("-f", "--src_file", help="The location of the file to be processed.")

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


def proc_file(file_name):
    with open(file_name) as d:
        nodups_lines = ['']
        for line in d:
            line = line.strip()
            if len(line) == 0:
                continue
            elif line == nodups_lines[-1]:
                continue
            else:
                nodups_lines.append(line)
    print('Completed reading {}.\n'.format(file_name))
    f_out_name = create_out_fname(file_name, suffix='_nodups')
    list_to_file(nodups_lines[1:], f_out_name)
    print('Wrote {}.\n'.format(f_out_name))


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
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
