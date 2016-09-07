#!/usr/bin/env python
"""
Given a file with columns of data (comma or space separated):
return a file that has lines based on combine 2 columns of the data, optionally adding a prefix, middle, or suffix
"""

from __future__ import print_function

import argparse
import csv
import sys
from md_utils.md_common import (InvalidDataError, warning, process_cfg,
                                list_to_csv, IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, read_csv, conv_str_to_func)
try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError, ParsingError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError, ParsingError

__author__ = 'hbmayes'


# Config File Sections
MAIN_SEC = 'main'
SECTIONS = [MAIN_SEC]

# Config keys
FILE_TO_PROCESS = 'file'
COL1 = 'col1'
COL2 = 'col2'
COL1_CONV = 'col1_conv'
COL2_CONV = 'col2_conv'
DELIM = 'delimiter'
PREFIX = 'prefix'
MIDDLE = 'middle'
SUFFIX = 'suffix'
OUT_FILE = 'output_file_name'

# Defaults
DEF_CFG_FILE = 'comb_col.ini'
DEF_FILE = 'filtered_comb.csv'
DEF_OUT = 'comb_col.txt'
DEF_DELIMITER = ','
DEF_PREFIX = ''
DEF_MIDDLE = ''
DEF_SUFFIX = ''

DEF_CFG_VALS = {DELIM: DEF_DELIMITER,
                OUT_FILE: DEF_OUT,
                PREFIX: DEF_PREFIX,
                MIDDLE: DEF_MIDDLE,
                SUFFIX: DEF_SUFFIX,
                COL1_CONV: None,
                COL2_CONV: None,
                }
REQ_KEYS = {COL1: str,
            COL2: str,
            }


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
        if not good_files:
            raise IOError('Could not read file {}'.format(floc))
        main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS, int_list=False)
    except (ParsingError, KeyError) as e:
        raise InvalidDataError(e)
    # Check the config file does not have sections that will be ignored
    for section in config.sections():
        if section not in SECTIONS:
            warning("Found section '{}', which will be ignored. Expected section names are: {}"
                    .format(section, ", ".join(SECTIONS)))
    # # Validate conversion input
    for conv in [COL1_CONV, COL2_CONV]:
        if main_proc[conv]:
            main_proc[conv] = conv_str_to_func(main_proc[conv])
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
                                                 'specifications from a configuration file, it combines data from '
                                                 'two columns per row and outputs that to a new row, adding a '
                                                 'prefix, middle (string joining the two columns), and suffix, if '
                                                 'supplied. The user can also specify that the column information be '
                                                 'converted (i.e. to an int).')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)
    parser.add_argument("-f", "--file", help="The location of the file with the column data to combine. "
                                             "The default file name is {}, "
                                             "located in the current directory".format(DEF_FILE),
                        default=DEF_FILE)
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


def process_file(file_to_process, cfg):
    """
    Will complete the work of this script based on the provided cfg
    @param file_to_process: the file with column to be combined
    @param cfg: the configuration of this run
    @return: errors or nothing
    """
    to_print = []

    # determine if any type conversion has been specified & create conv dict if needed
    if cfg[COL1_CONV] is None and cfg[COL2_CONV] is None:
        conv_dict = None
    else:
        conv_dict = {}
        if cfg[COL1_CONV] is not None:
            conv_dict[cfg[COL1]] = cfg[COL1_CONV]
        if cfg[COL2_CONV] is not None:
            conv_dict[cfg[COL2]] = cfg[COL2_CONV]

    raw_col_data = read_csv(file_to_process, data_conv=conv_dict, quote_style=csv.QUOTE_NONNUMERIC)
    for header in cfg[COL1], cfg[COL2]:
        if header not in raw_col_data[0]:
            raise InvalidDataError("Specified column header '{}' was not found in file: {}"
                                   "".format(header, file_to_process))
    for row in raw_col_data:
        to_print.append(["".join(map(str, [cfg[PREFIX], row[cfg[COL1]], cfg[MIDDLE], row[cfg[COL2]], cfg[SUFFIX]]))])

    list_to_csv(to_print, cfg[OUT_FILE], delimiter=',', quote_style=csv.QUOTE_MINIMAL)


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config
    try:
        process_file(args.file, cfg)
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
