#!/usr/bin/env python
"""
This program sets up scripts for running NAMD
"""

from __future__ import print_function

import argparse
import os
import sys
from collections import OrderedDict

from md_utils.fill_tpl import OUT_DIR, TPL_VALS, fill_save_tpl
from md_utils.md_common import (InvalidDataError, warning,
                                IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, read_tpl)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError, ParsingError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError, ParsingError

__author__ = 'hbmayes'

# Constants #
TYPE = "type"
CPU = "cpu"
GPU = "gpu"
OTHER = 'other'
TYPES = [CPU, GPU, OTHER]
OUT_FILE = 'output_name'

RUN = "runtime"
NAME = 'name'
INPUT_NAME = "input_name"
FIRST = 'first'

# Defaults
DEF_TYPE = CPU
DEF_CPU_TPL_FILE = 'make_prod_cpu.tpl'
DEF_GPU_TPL_FILE = 'make_prod_gpu.tpl'
DEF_CPU_OUT_FILE = 'make_prod_cpu.ini'
DEF_GPU_OUT_FILE = 'make_prod_gpu.ini'
DEF_RUN = 1
DEF_FIRST = 1
DEF_NAME = 'test'
DEF_INPUT_NAME = 'input'


def validate_args(args):
    """
    Check the expected arguments for valid input
    :param args:
    :return:
    """

    tpl_vals = OrderedDict()

    if args.config_tpl is None:
        # If more allowed TYPES are added, more default specs will be needed.
        if args.type is OTHER:
            raise InvalidDataError("User must specify a 'config_tpl' when the run 'type' is '{}'".format(OTHER))
        if args.type is GPU:
            args.config_tpl = DEF_GPU_TPL_FILE
        else:
            args.config_tpl = DEF_CPU_TPL_FILE
    if not os.path.isfile(args.config_tpl):
        raise InvalidDataError("Input error: could not find the specified "
                               "'config_tpl' file '{}'.".format(args.config_tpl))

    if args.file_out_name is None:
        # If more allowed TYPES are added, more default specs will be needed.
        if args.type is OTHER:
            raise InvalidDataError("User must specify a 'file_out_name' when the run 'type' is '{}'".format(OTHER))
        if args.type is GPU:
            args.file_out_name = DEF_GPU_OUT_FILE
        else:
            args.file_out_name = DEF_CPU_OUT_FILE

    # args.config
    int_var_dict = {FIRST: args.first, RUN: args.run}
    for variable_name, req_pos_int in int_var_dict.items():
        if req_pos_int < 1:
            raise InvalidDataError("Input error: the integer value for '{}' must be > 1.".format(variable_name))
        tpl_vals[variable_name] = req_pos_int

    tpl_vals[NAME] = args.name

    if args.file_out_name:
        file_out_name = args.file_out_name
    elif args.type == CPU:
        file_out_name = DEF_CPU_OUT_FILE
    elif args.type == GPU:
        file_out_name = DEF_GPU_OUT_FILE
    else:
        # only other option is that use selected OTHER but didn't give a name of a file
        if args.type == OTHER:
            raise InvalidDataError("Input error: a 'file_out_name' must be specified when "
                                   "the run type is '{}'.".format(OTHER))
        # we covered all the cases here now, so the next sentence is not actually required...
        raise InvalidDataError("Input error: a 'file_out_name' must be specified.")

    out_dir = args.out_dir
    if out_dir:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
    else:
        out_dir = os.path.dirname(args.config_tpl)

    cfg = {OUT_DIR: out_dir, TPL_VALS: tpl_vals, OUT_FILE: file_out_name}
    args.config = cfg
    # fill_tpl_ordered_dict.update
        #
        # val_ordered_dict = process_tpl_vals(config.items(section))
        # if section == TPL_EQS_SEC:
        #     # just keep the names, so we know special processing is required
        #     proc[TPL_EQ_PARAMS] = val_ordered_dict.keys()
        # proc[TPL_VALS].update(val_ordered_dict)


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    # --type cpu --run 1 --name test --input_name 7.1 --first 1
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Command-line NAMD template script editor.')

    # only certain types allowed; checks that only one of those is chosen. Thus, any type typos are caught
    parser.add_argument("-t", "--type", help="The type of job needed. Valid options are {}. "
                                             "The default option is {}.".format(TYPES, DEF_TYPE),
                        choices=TYPES, default=DEF_TYPE)

    parser.add_argument("-c", "--config_tpl", help="Template file to be used in generating the configuration file. "
                                                   "By default, the program will look in the current directory for a "
                                                   "template file named {} for {} jobs "
                                                   "and {} for {} jobs. This option allows the user to choose a "
                                                   "different template file from these defaults. It is required if "
                                                   "the job type is {}.'".format(DEF_CPU_TPL_FILE, CPU,
                                                                                 DEF_GPU_TPL_FILE, GPU, OTHER),
                        default=None)
    parser.add_argument("-d", "--out_dir", help="Output file directory folder. Default is the directory is where the "
                                                "template file is located, which in turn defaults to the current "
                                                "directory.",
                        default=None)

    parser.add_argument("-f", "--first", help="Value for created template: first (integer). "
                                              "Default is {}.".format(DEF_FIRST),
                        type=int, default=DEF_FIRST)

    parser.add_argument("-i", "--input_name", help="Value for created template: input_name. "
                                                   "Default is {}.".format(DEF_INPUT_NAME),
                        default=DEF_INPUT_NAME)

    parser.add_argument("-n", "--name", help="Value for created template: name. "
                                             "Default is {}.".format(DEF_NAME),
                        default=DEF_NAME)

    parser.add_argument("-o", "--file_out_name", help="The name of the configuration file to be created. "
                                                      "By default, the program will create a file named {} "
                                                      "for '{}' jobs "
                                                      "and {} for {} jobs. This option allows the user to choose a "
                                                      "different name from these defaults. It is required if "
                                                      "the job type is {}.'".format(DEF_CPU_OUT_FILE, CPU,
                                                                                    DEF_GPU_OUT_FILE, GPU, OTHER),
                        default=None)
    parser.add_argument("-r", "--run", help="Value for created template: run length (integer; "
                                            "default is {}.".format(DEF_RUN),
                        type=int, default=DEF_RUN)

    args = None
    try:
        args = parser.parse_args(argv)
        validate_args(args)
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


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config
    tpl_name = args.config_tpl
    filled_tpl_name = args.file_out_name
    try:
        fill_save_tpl(cfg, read_tpl(tpl_name), cfg[TPL_VALS], tpl_name, filled_tpl_name)
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
