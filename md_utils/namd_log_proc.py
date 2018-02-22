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
from md_utils.col_stats import main as col_stats

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
RUN_PAT = re.compile(r"^ETITLE:.*")
ENERGY_PAT = re.compile(r"^ENERGY: .*")
PERFORMANCE_PAT = re.compile(r"^TIMING: .*")

E_TOTAL = 'E_totalP'
E_BOND = 'E_bond'
E_ANGL = 'E_angl'
E_DIHED = 'E_dihed'
E_IMPRO = 'E_impro'
E_VDWL = 'E_vdwl'
TEMP = 'Temp'
PRESS = 'Press'
PERFORMANCE = 'time/ns'

LOG_FIELDNAMES = [FILE_NAME, TIMESTEP]


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
    parser.add_argument("-d", "--dihedral", help="Flag to collect dihedral energy data.",
                        action='store_true', default=False)
    parser.add_argument("-t", "--total", help="Flag to collect total potential energy data.", action='store_true', default=False)
    parser.add_argument("-p", "--performance", help="Flag to collect performance data.",
                        action='store_true', default=False)
    parser.add_argument("-s", "--step", help="Timestep to begin logging quantities. Default is none", default=None)
    parser.add_argument("--stats", help="Flag to automatically generate statistics from the data.", action='store_true', default=False)

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
        if ((args.dihedral or args.total) and args.performance):
            raise InvalidDataError("Script is not currently configured to accept both energy data ('-s' or '-t') and "
                                   "performance data ('-p'). Please select only one.")
        if not (args.dihedral or args.performance or args.total):
            raise InvalidDataError(
                "Did not choose to output dihedral data ('-s'), total potential energy ('-t'), or performance data ('-p'). "
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


def process_log(log_file, dihedral, total, performance, step):
    """
    Gather key info from log file
    @param log_file: name of log file
    @return: lists of dicts of key data extracted; 1 dict per timestep and/or dihedral
    """
    result_list = []
    file_root = get_fname_root(log_file)

    with open(log_file) as l_file:
        reading_data = False
        if not step:
            first_step = True
        else:
            first_step = False
            step_int = int(step)
        result_dict = {}
        for line in l_file:
            line = line.strip()
            if RUN_PAT.match(line):
                reading_data = True
                result_dict[FILE_NAME] = file_root
            if not first_step:
                if ENERGY_PAT.match(line):
                    s_line = line.split()
                    if int(s_line[1]) >= step_int:
                        first_step = True
            if reading_data and first_step:
                if dihedral and total and ENERGY_PAT.match(line):
                    s_line = line.split()
                    result_dict[TIMESTEP] = int(s_line[1])
                    result_dict[E_DIHED] = float(s_line[4])
                    result_dict[E_TOTAL] = float(s_line[13])
                    result_list.append(dict(result_dict))
                elif dihedral and ENERGY_PAT.match(line):
                    s_line = line.split()
                    result_dict[TIMESTEP] = int(s_line[1])
                    result_dict[E_DIHED] = float(s_line[4])
                    result_list.append(dict(result_dict))
                elif performance and PERFORMANCE_PAT.match(line):
                    s_line = line.replace("/", " ").split()
                    result_dict[TIMESTEP] = int(s_line[1])
                    result_dict[PERFORMANCE] = float(s_line[4])*500000/3600
                    result_list.append(dict(result_dict))
                elif total and ENERGY_PAT.match(line):
                    s_line = line.split()
                    result_dict[TIMESTEP] = int(s_line[1])
                    result_dict[E_TOTAL] = float(s_line[13])
                    result_list.append(dict(result_dict))

    return result_list


def process_log_files(source_name, log_file_list, print_dihedral_info, print_total_info, print_performance_info, step, stats):
    """
    Loops through all files and prints output
    @param source_name: the source name to use as the base for creating an outfile name
    @param log_file_list: list of file names to read and process
    """

    result_list = []
    field_names = LOG_FIELDNAMES.copy()
    if print_dihedral_info and print_total_info:
        field_names += [E_DIHED, E_TOTAL]
        out_fname = create_out_fname(source_name, suffix='_energy', ext=".csv")
    elif print_dihedral_info:
        field_names += [E_DIHED]
        out_fname = create_out_fname(source_name, suffix='_dihedral', ext=".csv")
    elif print_total_info:
        field_names += [E_TOTAL]
        out_fname = create_out_fname(source_name, suffix='_total', ext=".csv")
    elif print_performance_info:
        field_names += [PERFORMANCE]
        out_fname = create_out_fname(source_name, suffix='_performance', ext=".csv")

    for log_file in log_file_list:
        result_list += process_log(log_file, print_dihedral_info, print_total_info, print_performance_info, step)

    if len(result_list) == 0:
        warning("Found no log data to process from: {}".format(source_name))
    else:
        write_csv(result_list, out_fname, fieldnames=field_names, extrasaction="ignore")
    if stats:
        col_stats(["-n", "-f", out_fname])


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    try:
        process_log_files(args.source_name, args.file_list, args.dihedral, args.total, args.performance, args.step, args.stats)
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
