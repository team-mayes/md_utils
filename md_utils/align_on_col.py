#!/usr/bin/env python
"""
For combining data from multiple files based on a common timestep. All other data will be ignored or, if in logging
mode, printed to a log file.
"""

from __future__ import print_function
from collections import defaultdict
import logging
import sys
import argparse
import six

from md_utils.md_common import InvalidDataError, warning, read_csv_to_dict, write_csv

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('align_col')
logging.basicConfig(filename='align_col.log', filemode='w', level=logging.DEBUG)


# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3


# Constants #

# Defaults
DEF_CMP_FILE = 'compare_list.txt'
DEF_ALIGN_COL_NAME = 'timestep'
DEF_OUT_FILE = 'combined_data.csv'


def read_cmp_file(c_file):
    with open(c_file) as f:
        return f.readlines()


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Make combine output from multiple files, with a common column '
                                                 'name, printing only data from common column values. ')
    parser.add_argument("-f", "--compare_file_list", help="The location of the file that lists the files to be "
                                                          "combined, listing one file per line. "
                                                          "The default file name is {}, located in the "
                                                          "directory where the program as run.".format(DEF_CMP_FILE),
                        default=DEF_CMP_FILE, type=read_cmp_file)
    parser.add_argument("-n", "--col_name", help="The common column name in the files used as the key to combine "
                                                 "files. The default file name is {}.".format(DEF_ALIGN_COL_NAME),
                        default=DEF_ALIGN_COL_NAME)
    parser.add_argument("-o", "--out_name", help="The output file name. The default is {}.".format(DEF_OUT_FILE),
                        default=DEF_OUT_FILE)
    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    # except KeyError as e:
    #     warning("Input data missing:", e)
    #     parser.print_help()
    #     return args, INPUT_ERROR

    return args, GOOD_RET


def process_files(comp_f_list, col_name, f_out):
    """
    Want to grab the timestep, first and 2nd mole found, first and 2nd ci^2
    print the timestep, residue ci^2
    @param comp_f_list: list of file names to process
    @param col_name: name of column to use for alignment
    @param f_out: name of file to be created
    @return: @raise InvalidDataError:
    """
    timesteps = None
    headers = []
    all_dicts = defaultdict(dict)
    new_dict = {}
    for line in comp_f_list:
        s_line = line.strip()
        if len(s_line) > 0:
            new_dict = read_csv_to_dict(s_line, col_name)
            if timesteps is None:
                timesteps = new_dict.keys()
            else:
                timesteps = set(timesteps).intersection(new_dict.keys())
            new_dict_keys = six.next(six.itervalues(new_dict)).keys()
            # Get the keys for the inner dictionary; diff methods for python 2 and 3 so use six
            for key in new_dict_keys:
                if key in headers:
                    if key != col_name:
                        warning("Non-unique column name {} found in {}. "
                                "Values will be overwritten.".format(key, s_line))
                else:
                    headers.append(key)
        for new_key in new_dict.items():
            all_dicts[new_key[0]].update(new_key[1])

    final_dict = []
    for key in sorted(timesteps):
        final_dict.append(all_dicts[key])

    # Possible to have no overlap in align column
    if len(final_dict) > 0:
        # make sure col_name appears first by taking it out before sorting
        headers.remove(col_name)
        write_csv(final_dict, f_out, [col_name] + sorted(headers))

    else:
        raise InvalidDataError("No common values found for column {} among all files. "
                               "No output is created.".format(col_name))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    try:
        process_files(args.compare_file_list, args.col_name, args.out_name)
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
