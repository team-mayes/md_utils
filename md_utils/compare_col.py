#!/usr/bin/env python
"""
Given a file with columns of data (comma or space separated):
return a file that has a RMSD from comparing it to another file.
"""

from __future__ import print_function

import argparse
import csv
import sys
import numpy as np
from md_utils.md_common import (InvalidDataError, warning,
                                IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, read_csv,
                                read_csv_header, create_out_fname, write_csv)
try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError, ParsingError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError, ParsingError

__author__ = 'hbmayes'


# Constants #


# Defaults
DEF_CFG_FILE = 'filter_col.ini'
DEF_ARRAY_FILE = 'column_data.csv'
DEF_BASE_FILE = 'base_data.csv'
DEF_DELIMITER = ','
INDEX = 'index'
RMSD = 'rmsd'


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in files containing a header with columns of data. Using '
                                                 'specifications from a configuration file, it compares rows and '
                                                 'adds an RMSD to the comparison file.')

    parser.add_argument("-f", "--file", help="The location of the file with the dimensions with one line per vector, "
                                             "space-separated, containing at least two lines. The default file is {}, "
                                             "located in the current directory".format(DEF_ARRAY_FILE),
                        default=DEF_ARRAY_FILE)

    parser.add_argument("-b", "--base_file", help="The location of the file values used for comparison. There should "
                                                  "be two lines: a column headers followed by values. "
                                                  "The default file is {}, "
                                                  "located in the current directory".format(DEF_BASE_FILE),
                        default=DEF_BASE_FILE)

    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning(e)
        parser.print_help()
        return args, IO_ERROR
    except (InvalidDataError, SystemExit) as e:
        if hasattr(e, 'code') and e.code == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def process_file(base_file, data_file):
    # TODO: add in reading vectors
    base_dict = read_csv(base_file, quote_style=csv.QUOTE_NONNUMERIC)[0]
    data_dict_list = read_csv(data_file, quote_style=csv.QUOTE_NONNUMERIC)

    data_headers = [INDEX, RMSD] + read_csv_header(data_file)

    num_vals = len(base_dict.values())
    for data_id, data_dict in enumerate(data_dict_list):
        rmsd = 0.0
        for key, val in base_dict.items():
            try:
                rmsd += (data_dict[key] - val)**2
            except KeyError:
                raise InvalidDataError("Could not find key '{}' from base file in compared data file.".format(key))

        data_dict[INDEX] = data_id
        data_dict[RMSD] = round((rmsd/num_vals)**0.5, 2)

    out_name = create_out_fname(data_file, prefix=RMSD + '_')
    write_csv(data_dict_list, out_name, data_headers)


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    try:
        process_file(args.base_file, args.file)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except (ValueError, InvalidDataError) as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
