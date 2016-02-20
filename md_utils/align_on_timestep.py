#!/usr/bin/env python
"""
For combining data from multiple files based on a common timestep. All other data will be ignored or, if in logging
mode, printed to a log file.
"""

from __future__ import print_function

import ConfigParser
import logging
import re
import os
import numpy as np
from md_utils.md_common import list_to_file, InvalidDataError, warning, to_int_list, create_out_suf_fname, conv_raw_val

import sys
import argparse

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('align_timestep')
logging.basicConfig(filename='align_timestep.log', filemode='w', level=logging.DEBUG)


# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3


# Constants #

# Config File Sections
MAIN_SEC = 'main'

# Config keys
COMPARE_FILE = 'compare_file_list'

# Defaults
DEF_CFG_FILE = 'align_timestep.ini'
# Set notation
DEF_CFG_VALS = {COMPARE_FILE: 'evb_list.txt', }
REQ_KEYS = { }


def process_cfg(raw_cfg):
    """
    Converts the given raw configuration, filling in defaults and converting the specified value (if any) to the
    default value's type.
    :param raw_cfg: The configuration map.
    :return: The processed configuration.
    """
    proc_cfg = {}
    try:
        for key, def_val in DEF_CFG_VALS.items():
            proc_cfg[key] = conv_raw_val(raw_cfg.get(key), def_val)
    except Exception as e:
        logger.error('Problem with default config vals on key %s: %s', key, e)
    try:
        for key, type_func in REQ_KEYS.items():
            proc_cfg[key] = type_func(raw_cfg[key])
    except Exception as e:
        logger.error('Problem with required config vals on key %s: %s', key, e)


    # If I needed to make calculations based on values, get the values as below, and then
    # assign to calculated config values
    return proc_cfg


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
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)))
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Make combine output from two files, printing only common timesteps.'
                                                 'This program is more efficient if it reads the file with fewer '
                                                 'timesteps first.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "See the example file /test/test_data/evbd2d/align_timestep.ini. "
                                               "The default file name is align_timestep.ini, located in the "
                                               "base directory where the program as run.",
                        default=DEF_CFG_FILE, type=read_cfg)
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

def process_files(cfg):
    """
    Want to grab the timestep, first and 2nd mole found, first and 2nd ci^2
    print the timestep, residue ci^2
    @param cfg: configuration data read from ini file
    @return: @raise InvalidDataError:
    """
    with open(cfg[COMPARE_FILE]) as f:
        for file_line in f.readlines():
            files = [x.strip() for x in file_line.split(',')]
            print(files)
            time_dict = {}
            print_lines = []
            with open(files[0]) as d:
                for line in d.readlines():
                    split_line = [x.strip() for x in line.split(',')]
                    time_dict[split_line[0]] = split_line[1:]
            with open(files[1]) as e:
                for line in e.readlines():
                    split_line = [x.strip() for x in line.split(',')]
                    if split_line[0] in time_dict:
                        print_lines.append(','.join([split_line[0]] + time_dict[split_line[0]] + split_line[1:]))
                    else:
                        logger.debug("Timestep {} found in second file, but not first. Will discard second file "
                                     "line {}.".format(split_line[0], line.strip()))

            d_out = create_out_suf_fname(files[0], '_plus', ext='.csv')
            list_to_file(print_lines, d_out)
            print('Wrote file: {}'.format(d_out))
    return


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    # TODO: did not show the expected behavior when I didn't have a required cfg in the ini file
    if ret != GOOD_RET:
        return ret

    # TODO: Make so can combine multiple files
    # TODO: Make user specify the file with fewer lines

    # Read template and dump files
    cfg = args.config
    try:
        process_files(cfg)
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
