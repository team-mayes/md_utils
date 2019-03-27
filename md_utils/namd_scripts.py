#!/usr/bin/env python
"""
This program sets up scripts for running NAMD
"""

from __future__ import print_function

import argparse
import os
import re
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
OUT_FILE = 'file_out_name'

RUN = 'runtime'
JOB_NAME = 'name'
INPUT_NAME = 'input_name'
OUTPUT = 'output_name'
STRUCTURE = 'structure'
COORDINATES = 'coordinates'

# Defaults
DEF_TYPE = CPU
DEF_CPU_TPL_FILE = 'make_prod_cpu.tpl'
DEF_GPU_TPL_FILE = 'make_prod_gpu.tpl'
DEF_CPU_OUT_FILE = 'make_prod_cpu.ini'
DEF_GPU_OUT_FILE = 'make_prod_gpu.ini'
DEF_RUN = 2
DEF_JOB_NAME = 'test'
DEF_INPUT_NAME = 'input'
DEF_OUTPUT = 'output'
DEF_STRUCTURE = 'test.psf'
DEF_COORDINATES = 'test.pdb'

# Restart Patterns
OUT_PAT = re.compile(r"^outputname.*")
SET_OUT_PAT = re.compile(r"^set output.*")
IN_PAT = re.compile(r"^set input.*")
RUN_PAT = re.compile(r"^run.*")
FIRSTTIME_PAT = re.compile(r"^firsttimestep.*")
NUM_PAT = re.compile(r"^numsteps.*")
XSC_PAT = re.compile(r"^.*0 0 0.*")
JOB_PAT = re.compile(r"^.*--job-name.*")
SUBMIT_PAT = re.compile(r"^.*namd2.*")


# Local variable warnings are due to my taking shortcuts by
# knowing how NAMD input scripts and job files are structured

def make_restart(file, xsc_file=None):
    # TODO: restart pbs files as well as job files (won't be necessary in a short time)
    inp_file = file + '.inp'
    job_file = file + '.job'
    s_file = file.split(".")
    if len(s_file) < 3:
        restart_file = file + '.2.'
    else:
        s_file[2] = str(1 + int(s_file[2]))
        restart_file = ''
        for part in s_file:
            restart_file += part + '.'
    restart_inp = restart_file + 'inp'
    restart_job = restart_file + 'job'

    # process and write a restart inp file
    with open(inp_file, "rt") as fin:
        with open(restart_inp, "w") as fout:
            for line in fin:
                # TODO: not depend on outputname being specified before the inputname
                if OUT_PAT.match(line) or SET_OUT_PAT.match(line):
                    try:
                        outputname
                        fout.write(line)
                    except:
                        s_line = line.split()
                        outputname = s_line[-1].strip(";")
                        s_out = outputname.split(".")

                        if len(s_out) < 3:
                            new_out = outputname + '.2'
                        else:
                            new_out = s_out[0] + '.' + s_out[1] + '.' + str((int(s_out[2]) + 1))
                        fout.write(line.replace(outputname, new_out))
                elif IN_PAT.match(line):
                    s_line = line.split()
                    inputname = s_line[2].strip(";")
                    new_in = outputname + '.restart'
                    fout.write(line.replace(inputname, new_in))
                elif FIRSTTIME_PAT.match(line):
                    s_line = line.split()
                    current_step = s_line[1].strip(";")
                    if current_step != "$firsttime":
                        if xsc_file:
                            restart_xsc = xsc_file
                        else:
                            restart_xsc = new_in + '.xsc'
                        with open(restart_xsc, "rt") as xin:
                            for x_line in xin:
                                if x_line != '\n' and x_line[0] != '#':
                                    s_x_line = x_line.split()
                                    start_step = int(s_x_line[0])
                        fout.write(line.replace(current_step, str(start_step)))
                    else:
                        fout.write(line)
                elif RUN_PAT.match(line):
                    try:
                        start_step
                    except:
                        if xsc_file:
                            inputname = xsc_file
                        else:
                            inputname += '.xsc'
                        with open(inputname, "rt") as xin:
                            for x_line in xin:
                                if x_line != '\n' and x_line[0] != '#':
                                    s_x_line = x_line.split()
                                    current_step = s_x_line[0]

                    s_line = line.split()
                    run_step = int(s_line[1].split(";")[0])
                    steps_remaining = run_step - int(current_step) # This variable can be used for writing
                    # 'run' to input file or modifying the requested time in the job file
                    num_step = int(current_step) + run_step
                    ns = str(int(num_step / 500000))
                    output = 'numsteps    {:>14};            # {} ns'.format(num_step,ns)
                    fout.write(output)
                else:
                    fout.write(line)

    # process and write a restart job file
    # TODO: Make intelligent judgement about modifying the time requested
    with open(job_file, "rt") as fin:
        with open(restart_job, "w") as fout:
            for line in fin:
                if JOB_PAT.match(line):
                    line = line.rstrip()
                    # Restart train could potentially derail,
                    # but I'm depending on not failing too many consecutive times
                    # At that point human intervention is necessary
                    fout.write(line + '_restart\n')
                elif SUBMIT_PAT.match(line):
                    s_line = line.split()
                    for element in s_line:
                        if '.inp' in element:
                            old_inp = element
                        elif '.log' in element:
                            old_log = element
                    line = line.replace(old_inp, new_out + '.inp')
                    fout.write(line.replace(old_log, new_out + '.log'))
                else:
                    fout.write(line)
    print("Wrote file: {}".format(restart_inp))
    print("Wrote file: {}".format(restart_job))


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
    int_var_dict = {RUN: args.run}
    for variable_name, req_pos_int in int_var_dict.items():
        if req_pos_int < 1:
            raise InvalidDataError("Input error: the integer value for '{}' must be > 1.".format(variable_name))
        tpl_vals[variable_name] = req_pos_int

    tpl_vals[JOB_NAME] = args.job_name
    tpl_vals[INPUT_NAME] = args.input_name
    tpl_vals[OUTPUT] = args.output_name
    tpl_vals[STRUCTURE] = args.structure
    tpl_vals[COORDINATES] = args.coordinates

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

    args.config = {OUT_DIR: out_dir, TPL_VALS: tpl_vals, OUT_FILE: file_out_name}
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

    parser.add_argument("-i", "--input_name", help="Value for created template: input_name. "
                                                   "Default is {}.".format(DEF_INPUT_NAME),
                        default=DEF_INPUT_NAME)

    parser.add_argument("-n", "--job_name", help="Value for created template: name. "
                                                 "Default is {}.".format(DEF_JOB_NAME),
                        default=DEF_JOB_NAME)

    parser.add_argument("-o", "--file_out_name", help="The name of the configuration file to be created. "
                                                      "By default, the program will create a file named {} "
                                                      "for '{}' jobs "
                                                      "and {} for {} jobs. This option allows the user to choose a "
                                                      "different name from these defaults. It is required if "
                                                      "the job type is {}.'".format(DEF_CPU_OUT_FILE, CPU,
                                                                                    DEF_GPU_OUT_FILE, GPU, OTHER),
                        default=None)
    parser.add_argument("--output_name", help="Name for the NAMD output", default=DEF_OUTPUT)
    parser.add_argument("-r", "--run", help="Value for created template: run length (integer; "
                                            "default is {}.".format(DEF_RUN),
                        type=int, default=DEF_RUN)

    parser.add_argument("-s", "--structure", help="Name of the structure file; "
                                                  "default is {}.".format(DEF_STRUCTURE),
                        default=DEF_STRUCTURE)
    parser.add_argument("-co", "--coordinates", help="Name of the coordinates file; "
                                                     "default is {}.".format(DEF_COORDINATES),
                        default=DEF_COORDINATES)
    parser.add_argument("-re", "--restart",
                        help="Flag to generate a restart inp and job file from a provided job prefix. "
                             "This option preempts all other options.", default=None)
    parser.add_argument("-x", "--xsc", help="Path to extended system file. Default is to read from inp file.",
                        default=None)

    args = None
    try:
        args = parser.parse_args(argv)
        if not args.restart:
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

    try:
        if args.restart:
            make_restart(args.restart, args.xsc)
        else:
            fill_save_tpl(args.config, read_tpl(args.config_tpl), args.config[TPL_VALS],
                          args.config_tpl, args.file_out_name)
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
