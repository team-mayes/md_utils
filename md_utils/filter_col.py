#!/usr/bin/env python
"""
Given a file with columns of data (comma or space separated):
return a file that has lines filtered by specified min and max values
"""

from __future__ import print_function

import argparse
import sys
import numpy as np
# noinspection PyCompatibility
import ConfigParser

from md_utils.md_common import (InvalidDataError, warning,
                                create_out_fname, process_cfg, read_csv_to_list,
                                list_to_csv)

__author__ = 'hmayes'


# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3

# Constants #

# Config File Sections
MAIN_SEC = 'main'
MAX_SEC = 'max_vals'
MIN_SEC = 'min_vals'

# Defaults
DEF_CFG_FILE = 'filter_col_data.ini'
DEF_ARRAY_FILE = 'column_data.csv'
DEF_DELIMITER = ','
FILTER_HEADERS = 'filter_col_names'

DEF_CFG_VALS = {}
REQ_KEYS = {}


def check_vals(config, sec_name):
    """
    Reads the max or min vals section of the given config file,
    returning a dict containing the original string key paired with a float representing the max or min value.
    If there is no specified section, an empty dict is returned.  Invalid values result in DataExceptions.
    :param config: The parsed config file that contains a max and/or min section.
    :param sec_name: the name of the section with string/float pairs to digest
    :return: A dict mapping the original column key to the float limit value.
    """
    limit_vals = {}
    limit_val = np.nan
    col_name = None
    try:
        for col_name, limit_val in config.items(sec_name):
            # if col_name in limit_vals:
            #     if limit_vals[col_name] != limit_val:
            #         raise InvalidDataError("Columns name '{}' appeared more than once in the '{}' section of the "
            #                                "configuration file.".format(col_name, sec_name))
            limit_vals[col_name] = float(limit_val)
    except ConfigParser.NoSectionError:
        warning("No '{}' section. Program will continue.".format(sec_name))
    except ValueError as e:
        raise InvalidDataError("For key '{}', could not convert value '{}' to a float.".format(limit_val, col_name), e)
    return limit_vals


def read_cfg(floc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param floc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser.ConfigParser()
    good_files = config.read(floc)
    if not good_files:
        raise IOError('Could not read file {}'.format(floc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS, int_list=False)
    for section in [MAX_SEC, MIN_SEC]:
        main_proc[section] = check_vals(config, section)
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in a file containing a header with columns of data. Using '
                                                 'specifications from a configuration file, it filters rows based '
                                                 'on column min and/or max values, and prints a file of the filtered '
                                                 'data.')

    parser.add_argument("-f", "--file", help="The location of the file with the dimensions with one line per vector, "
                                             "space-separated, containing at least two lines. The default file is {}, "
                                             "located in the current directory".format(DEF_ARRAY_FILE),
                        default=DEF_ARRAY_FILE)

    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)

    parser.add_argument("-d", "--delimiter", help="Delimiter. Default is '{}'".format(DEF_DELIMITER),
                        default=DEF_DELIMITER)

    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning(e)
        parser.print_help()
        return args, IO_ERROR
    except (InvalidDataError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def process_file(data_file,  mcfg, delimiter=','):
    list_vectors, headers = read_csv_to_list(data_file, delimiter=delimiter, header=True)

    col_index_dict = {}
    for section in [MAX_SEC, MIN_SEC]:
        col_index_dict[section] = {}
        for key, val in mcfg[section].items():
            if key in headers:
                # Parser already made sure that unique entries
                col_index_dict[section][headers.index(key)] = val
            else:
                raise InvalidDataError("Key '{}' found in configuration file but not in data file: "
                                       "{}".format(key, data_file))

    initial_row_num = len(list_vectors)
    filtered_vectors = []
    for row in list_vectors:
        keep_row = True
        for col, max_val in col_index_dict[MAX_SEC].items():
            if row[col] > max_val:
                keep_row = False
        for col, min_val in col_index_dict[MIN_SEC].items():
            if row[col] < min_val:
                keep_row = False
        if keep_row:
            filtered_vectors.append(row)

    print("Keeping {} of {} rows based on filtering criteria".format(len(filtered_vectors), initial_row_num))

    f_name = create_out_fname(data_file, prefix='filtered_', ext='.csv')
    list_to_csv([headers] + filtered_vectors, f_name, delimiter=',')


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config
    try:
        process_file(args.file, cfg, delimiter=args.delimiter)
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
