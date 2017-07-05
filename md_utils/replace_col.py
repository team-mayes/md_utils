#!/usr/bin/env python
"""
Given a file with columns of data (comma or space separated):
return a file that has lines filtered by specified min and max values
"""

from __future__ import print_function

import argparse
import os
import sys
import numpy as np
from md_utils.md_common import (InvalidDataError, warning,
                                create_out_fname, process_cfg, read_csv_to_list,
                                list_to_csv, IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA,
                                find_files_by_dir)
try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError, ParsingError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError, ParsingError

__author__ = 'hbmayes'


# Constants #

# Config File Sections
MAIN_SEC = 'main'
MAX_SEC = 'max_vals'
MIN_SEC = 'min_vals'

SUB_SECTIONS = [MAX_SEC, MIN_SEC]
SECTIONS = [MAIN_SEC] + SUB_SECTIONS
FILE_PAT = 'file_pattern'

# Defaults
DEF_CFG_FILE = 'replace_col.ini'
DEF_ARRAY_FILE = 'column_data.csv'
DEF_DELIMITER = ','
FILTER_HEADERS = 'filter_col_names'
DEF_FILE_PAT = 'seed*csv'

DEF_CFG_VALS = {FILE_PAT: DEF_FILE_PAT}
REQ_KEYS = {}

BINS = 'bin_array'
MOD = 'modulo'
QUOT = 'quotient'


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
            # I don't test for non-unique column name because, if a col_name appears twice, the parser has already
            # handled it by overwriting the value for that key
            limit_vals[col_name] = float(limit_val)
    except NoSectionError:
        # not a problem
        pass
    except ValueError:
        raise InvalidDataError("For section '{}' key '{}', could not convert value '{}' to a float."
                               .format(sec_name, col_name, limit_val, ))
    return limit_vals


def read_cfg(floc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param floc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser()
    try:
        good_files = config.read(floc)
    except ParsingError as e:
        raise InvalidDataError(e)
    if not good_files:
        raise IOError('Could not read file {}'.format(floc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS, int_list=False)
    # Check that there is a least one subsection, or this script won't do anything. Check that all sections given
    # are expected or alert user that a given section is ignored (thus catches types, etc.)
    no_work_to_do = True
    for section in config.sections():
        if section in SECTIONS:
            if section in SUB_SECTIONS:
                if len(config.items(section)) > 0:
                    no_work_to_do = False
        else:
            warning("Found section '{}', which will be ignored. Expected section names are: {}"
                    .format(section, ", ".join(SECTIONS)))
    if no_work_to_do:
        warning("No filtering will be applied as no criteria were found for the expected subsections ({})."
                "".format(", ".join(SUB_SECTIONS)))
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
                                                 'specifications from a configuration file, it changes values in rows '
                                                 'based on column min and/or max values, and overwrites the original '
                                                 'file.')

    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)

    parser.add_argument("-d", "--delimiter", help="Delimiter separating columns in the FILE to be edited. "
                                                  "The default is: '{}'".format(DEF_DELIMITER),
                        default=DEF_DELIMITER)
    parser.add_argument("-b", "--base_dir", help="The starting point for a file search "
                                                 "(defaults to current directory)",
                        default=os.getcwd())
    parser.add_argument("-f", "--src_file", help="The single file to read from (takes precedence "
                                                 "over base_dir)")

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


def process_file(data_file,  mcfg, delimiter=','):
    list_vectors, headers = read_csv_to_list(data_file, delimiter=delimiter, header=True)

    col_index_dict = {}
    for section in SUB_SECTIONS:
        col_index_dict[section] = {}
        for key, val in mcfg[section].items():
            if key in headers:
                # Parser already made sure that unique entries
                col_index_dict[section][headers.index(key)] = val
            else:
                raise InvalidDataError("Key '{}' found in configuration file but not in data file: "
                                       "{}".format(key, data_file))

    edited_vectors = []
    for row in list_vectors:
        for col, max_val in col_index_dict[MAX_SEC].items():
            if row[col] > max_val:
                row[col] = max_val
        for col, min_val in col_index_dict[MIN_SEC].items():
            if row[col] < min_val:
                row[col] = min_val
        edited_vectors.append(row)

    f_name = create_out_fname(data_file, ext='.csv')
    list_to_csv([headers] + edited_vectors, f_name, delimiter=',')


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config
    try:

        if args.src_file is not None:
            process_file(args.src_file, cfg, delimiter=args.delimiter)
        else:
            found_files = find_files_by_dir(args.base_dir, cfg[FILE_PAT])
            # noinspection PyCompatibility
            for f_dir, files in found_files.iteritems():
                if not files:
                    warning("No files found for dir '{}'".format(f_dir))
                    continue
                for csv_path in ([os.path.join(f_dir, tgt) for tgt in files]):
                    process_file(csv_path, cfg, delimiter=args.delimiter)
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
