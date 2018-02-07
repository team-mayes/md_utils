#!/usr/bin/env python
# coding=utf-8
"""
Edit a FEP file to correct timestep data and remove statements falsely indicating new windows
"""

from __future__ import print_function
import os
import sys
import argparse
import re
import numpy as np
from md_utils.md_common import list_to_file, InvalidDataError, warning, process_cfg, create_out_fname, read_csv_dict, \
    print_qm_kind, create_element_dict, print_qm_links, list_to_csv

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser

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

# Config keys
FEP_FILE = 'fep_file'
FEP_NEW_FILE = 'new_fep_name'
OUT_BASE_DIR = 'output_directory'
SHIFT = 'timestep_shift'

# FEP file info
FEP_LINE_TYPE_LAST_CHAR = 'FEP_line_type_last_char'
FEP_TIMESTEP_LAST_CHAR = 'FEP_atom_num_last_char'
FEP_ELEC0_LAST_CHAR = 'FEP_atom_type_last_char'
FEP_ELEC1_LAST_CHAR = 'FEP_res_type_last_char'
FEP_VDW0_LAST_CHAR = 'FEP_mol_num_last_char'
FEP_VDW1_LAST_CHAR = 'FEP_x_last_char'
FEP_DE_LAST_CHAR = 'FEP_y_last_char'
FEP_DEAVG_LAST_CHAR = 'FEP_z_last_char'
FEP_TEMP_LAST_CHAR = 'FEP_last_temp_char'
FEP_DG_LAST_CHAR = 'FEP_last_element_char'
FEP_FORMAT = 'FEP_print_format'
COMMENT_FORMAT = 'Comment_print_format'

# Defaults
DEF_CFG_FILE = 'FEP_edit.ini'
DEF_CFG_VALS = {OUT_BASE_DIR: None,
                FEP_NEW_FILE: None,
                FEP_FORMAT: '{:10s} {:>6}{:>16}{:>15}{:>15}{:>15}{:>15}{:>15}{:>15}{:>15}',
                COMMENT_FORMAT: '{}',
                FEP_LINE_TYPE_LAST_CHAR: 10,
                FEP_TIMESTEP_LAST_CHAR: 18,
                FEP_ELEC0_LAST_CHAR: 33,
                FEP_ELEC1_LAST_CHAR: 48,
                FEP_VDW0_LAST_CHAR: 63,
                FEP_VDW1_LAST_CHAR: 78,
                FEP_DE_LAST_CHAR: 93,
                FEP_DEAVG_LAST_CHAR: 108,
                FEP_TEMP_LAST_CHAR: 123,
                FEP_DG_LAST_CHAR: 138,
                SHIFT: 500000,
                }
REQ_KEYS = {FEP_FILE: str,
            }

HEAD_CONTENT = 'head_content'
TIME_CONTENT = 'time_content'
TAIL_CONTENT = 'tail_content'
RUN_PAT = re.compile(r"^#START.*")


def read_cfg(f_loc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param f_loc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser()
    good_files = config.read(f_loc)
    if not good_files:
        raise IOError('Could not read file: {}'.format(f_loc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)

    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates a new version of a FEP file. Atoms will be numbered '
                                                 'starting from one. Options include renumbering molecules.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)
    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning(e)
        parser.print_help()
        return args, IO_ERROR
    except (KeyError, InvalidDataError, SystemExit) as e:
        if hasattr(e, 'code') and e.code == 0:
            return args, GOOD_RET
        warning("Input data missing:", e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def FEP_atoms_to_file(FEP_format, comment_format, list_val, fname, mode='w'):
    """
    Writes the list of sequences to the given file in the specified format for a PDB

    @param FEP_format: provides correct formatting
    @param list_val: The list of sequences to write.
    @param fname: The location of the file to write.
    @param mode: default is to write; can allow to append
    """
    with open(fname, mode) as w_file:
        for line in list_val:
            if line[0][0] == '#':
                w_file.write(comment_format.format(*line) + '\n')
            else:
                w_file.write(FEP_format.format(*line) + '\n')


def print_FEP(head_data, FEP_data, tail_data, file_name, file_format, comment_format):
    list_to_file(head_data, file_name)
    FEP_atoms_to_file(file_format, comment_format, FEP_data, file_name, mode='a')
    list_to_file(tail_data, file_name, mode='a', print_message=False)


def process_FEP(cfg):
    FEP_loc = cfg[FEP_FILE]
    FEP_data = {HEAD_CONTENT: [], TIME_CONTENT: [], TAIL_CONTENT: []}

    with open(FEP_loc) as f:
        time_content = []
        shifting_timesteps = False
        switch = False

        for line in f:
            line = line.strip()
            line_len = len(line)
            if line_len == 0:
                continue
            line_head = line[:cfg[FEP_LINE_TYPE_LAST_CHAR]]
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if switch and line_head[0:4] == '#NEW':
                switch = False
                shifting_timesteps = True
            elif not switch and line_head[0] == '#':
                line_struct = [line]
                time_content.append(line_struct)
                if RUN_PAT.match(line_head):
                    switch = True

            # atoms_content to contain everything but the xyz
            elif line_head == 'FepEnergy:':

                if shifting_timesteps:
                    timestep = int(line[cfg[FEP_LINE_TYPE_LAST_CHAR]:cfg[FEP_TIMESTEP_LAST_CHAR]]) + cfg[SHIFT]
                else:
                    timestep = int(line[cfg[FEP_LINE_TYPE_LAST_CHAR]:cfg[FEP_TIMESTEP_LAST_CHAR]])
                if int(timestep) == 1000000:
                    shifting_timesteps = False
                    switch = False
                elec0 = (line[cfg[FEP_TIMESTEP_LAST_CHAR]:cfg[FEP_ELEC0_LAST_CHAR]])
                elec1 = (line[cfg[FEP_ELEC0_LAST_CHAR]:cfg[FEP_ELEC1_LAST_CHAR]])
                vdw0 = (line[cfg[FEP_ELEC1_LAST_CHAR]:cfg[FEP_VDW0_LAST_CHAR]])
                vdw1 = (line[cfg[FEP_VDW0_LAST_CHAR]:cfg[FEP_VDW1_LAST_CHAR]])
                dE = (line[cfg[FEP_VDW1_LAST_CHAR]:cfg[FEP_DE_LAST_CHAR]])
                dEavg = (line[cfg[FEP_DE_LAST_CHAR]:cfg[FEP_DEAVG_LAST_CHAR]])
                temp = (line[cfg[FEP_DEAVG_LAST_CHAR]:cfg[FEP_TEMP_LAST_CHAR]])
                dG = (line[cfg[FEP_TEMP_LAST_CHAR]:cfg[FEP_DG_LAST_CHAR]])

                line_struct = [line_head, timestep, elec0, elec1, vdw0, vdw1, dE,
                               dEavg, temp, dG]
                time_content.append(line_struct)


                # tail_content to contain everything after the 'Atoms' section

    FEP_data[TIME_CONTENT] = time_content

    if cfg[FEP_NEW_FILE] is None:
        f_name = create_out_fname(cfg[FEP_FILE], suffix="_new", base_dir=cfg[OUT_BASE_DIR])
    else:
        f_name = create_out_fname(cfg[FEP_NEW_FILE], base_dir=cfg[OUT_BASE_DIR])
    print_FEP(FEP_data[HEAD_CONTENT], FEP_data[TIME_CONTENT], FEP_data[TAIL_CONTENT],
              f_name, cfg[FEP_FORMAT], cfg[COMMENT_FORMAT])


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config

    # Read and process FEP files
    try:
        process_FEP(cfg)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except (InvalidDataError, ValueError) as e:
        warning("Problems with input:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
