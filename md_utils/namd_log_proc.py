#!/usr/bin/env python
"""
From namd logs file(s), finds key output such as system energy and temperature
"""

from __future__ import print_function

import argparse
import os
import sys

import re

from md_utils.md_common import (InvalidDataError, warning, file_rows_to_list, IO_ERROR, GOOD_RET, INPUT_ERROR,
                                INVALID_DATA, get_fname_root, create_out_fname, write_csv)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError

__author__ = 'hmayes'


# Constants #

# For log file processing
SEC_TIMESTEP = 'timestep'

# For evb processing and output
FILE_NAME = 'filename'
TIMESTEP = 'timestep'
RUN_PAT = re.compile(r"^TCL: Running.*")
ENERGY_PAT = re.compile(r"^ENERGY: .*")

E_BOND = 'E_bond'
E_ANGL = 'E_angl'
E_DIHED = 'E_dihed'
E_IMPRO = 'E_impro'
E_VDWL = 'E_vdwl'
TEMP = 'Temp'
PRESS = 'Press'

LOG_FIELDNAMES = [FILE_NAME, TIMESTEP, E_DIHED]

def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='For each timestep, gather the energy information output by NAMD '
                                                 'in the log file.')
    parser.add_argument("-f", "--file", help="The log file to be processed.",
                        default=None)
    parser.add_argument("-l", "--list_file", help="The a file with a list of log files to be processes.",
                        default=None)
    parser.add_argument("-s", "--summary", help="Flag to collect summary data.",
                        action='store_true', default=False)
    parser.add_argument("-t", "--timestep", help="Flag to collect data per time step.",
                        action='store_true', default=False)
    args = None
    try:
        args = parser.parse_args(argv)
        if args.file is None:
            args.file_list = []
        else:
            if os.path.isfile(args.file):
                args.file_list = [args.file]
                args.source_name = args.file
            else:
                raise IOError("Could not find specified log file: {}".format(args.file))
        if args.list_file is not None:
            args.file_list += file_rows_to_list(args.list_file)
            args.source_name = args.list_file
        if len(args.file_list) < 1:
            raise InvalidDataError("Found no log file names to process. Specify one or more files as specified in "
                                   "the help documentation ('-h').")
        if not (args.summary or args.timestep):
            raise InvalidDataError("Did not choose either to output summary data ('-s') or data per timestep ('-t'). "
                                   "No output will be produced.")
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except (KeyError, InvalidDataError, SystemExit) as e:
        if hasattr(e, 'code') and e.code == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


def process_log(log_file):
    """
    Gather key info from log file
    @param log_file: name of log file
    @return: lists of dicts of key data extracted; 1 dict per timestep and/or summary
    """
    result_list = []
    file_root = get_fname_root(log_file)

    with open(log_file) as l_file:
        reading_data = False
        result_dict = {}
        for line in l_file:
            line = line.strip()
            if RUN_PAT.match(line):
                reading_data = True
                result_dict[FILE_NAME] = file_root
            elif reading_data:
                if ENERGY_PAT.match(line):
                    s_line = line.split()
                    result_dict[TIMESTEP] = int(s_line[1])
                    result_dict[E_DIHED] = float(s_line[4])
                    result_list.append(dict(result_dict))

    return result_list


def process_log_files(source_name, log_file_list, print_sum_info, print_ts_info):
    """
    Loops through all files and prints output
    @param source_name: the source name to use as the base for creating an outfile name
    @param log_file_list: list of file names to read and process
    """

    result_list = []
    out_fname = create_out_fname(source_name, suffix='_sum', ext=".csv")

    for log_file in log_file_list:
        result_list += process_log(log_file)

    if len(result_list) == 0:
        warning("Found no log data to process from: {}".format(source_name))
    else:
        write_csv(result_list, out_fname, LOG_FIELDNAMES, extrasaction="ignore")


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    try:
        process_log_files(args.source_name, args.file_list, args.summary, args.timestep)
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
