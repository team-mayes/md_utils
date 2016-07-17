#!/usr/bin/env python
"""
Adds a string to the beginning and end of a file.
"""

from __future__ import print_function
import logging
import sys
import argparse

from md_utils.md_common import InvalidDataError, create_out_fname, warning

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
DEF_NEW_FNAME = None


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in a file and counts the number of columns on the first line.')
    parser.add_argument("-f", "--file", help="The location of the file to be analyzed.")
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


def process_file(f_list, new_f_name):

    value_dict = {}

    print("hello world")

    with open(f_list) as f:
        for f_name in f.readlines():
            f_name = f_name.strip()
            with open(f_name) as d:
                for line in d.readlines():
                    # string2 = string1.strip('\n')
                    line = line.strip()
                    split_line = line.split()
                    entries = len(split_line)
                    # For this purpose, subtract 1 (hydronium) and divide by 3
                    water_mol_number = (entries - 1) / 3
                    if water_mol_number in value_dict:
                        value_dict[water_mol_number] += 1
                    else:
                        value_dict[water_mol_number] = 1

    if new_f_name is None:
        new_f_name = create_out_fname(f_list, suffix='_count')

    with open(new_f_name, 'w') as w_file:
        for key in value_dict:
            w_file.write(str(key) + "," + str(value_dict[key]) + "\n")
            print(key, value_dict[key])


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    # TODO: did not show the expected behavior when I didn't have a required cfg in the ini file
    if ret != GOOD_RET:
        return ret

    try:
        process_file(args.file, args.new_name)
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
