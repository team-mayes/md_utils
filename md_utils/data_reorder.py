#!/usr/bin/env python
"""
Creates pdb data files from lammps data files, given a template pdb file.
"""

from __future__ import print_function

import ConfigParser
from collections import defaultdict
import copy
import logging
import re
import numpy as np
import csv
from md_utils.md_common import list_to_file, InvalidDataError, seq_list_to_file, create_out_suf_fname, str_to_file, create_out_fname, warning
import sys
import argparse

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('data_reorder')
logging.basicConfig(filename='data_reorder.log', filemode='w', level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)



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
DATAS_FILE = 'data_list_file'
ATOM_ID_DICT_FILE = 'atom_reorder_dict_filename'

# data file info


# Defaults
DEF_CFG_FILE = 'data_reorder.ini'
# Set notation
DEF_CFG_VALS = {DATAS_FILE: 'data_list.txt',
                ATOM_ID_DICT_FILE: 'reorder_old_new.csv',
                }
REQ_KEYS = {
             }

# For data template file processing
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'

def to_int_list(raw_val):
    return_vals = []
    for val in raw_val.split(','):
        return_vals.append(int(val.strip()))
    return return_vals


def conv_raw_val(param, def_val):
    """
    Converts the given parameter into the given type (default returns the raw value).  Returns the default value
    if the param is None.
    :param param: The value to convert.
    :param def_val: The value that determines the type to target.
    :return: The converted parameter value.
    """
    if param is None:
        return def_val
    if isinstance(def_val, bool):
        return bool(param)
    if isinstance(def_val, int):
        return int(param)
    if isinstance(def_val, long):
        return long(param)
    if isinstance(def_val, float):
        return float(param)
    if isinstance(def_val, list):
        return to_int_list(param)
    return param


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
    parser = argparse.ArgumentParser(description='Reorders entries in a lammps data file, given a dictionary to reorder '
                                                 'the atoms (each line contains the old index (0-based) followed by the'
                                                 'new, in csv format.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format."
                                               "See the example file /test/test_data/data_reorder/data_reorder.ini. "
                                               "The default file name is data_reorder.ini, located in the "
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

def process_data_files(cfg):
    atom_id_dict_loc = cfg[ATOM_ID_DICT_FILE]
    atom_id_dict = {}
    # Read in the dictionary
    # Note: the dictionary is base 1. Since python arrays are base 0, subtract one.
    with open(atom_id_dict_loc) as csvfile:
        for line in csv.reader(csvfile):
            try:
                atom_id_dict[int(line[0]) - 1 ] = int(line[1]) - 1
            except ValueError as e:
                logger.debug("Could not convert line %s of file %s to two integers.", line, csvfile)

    # Prep for reading data files
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    atoms_pat = re.compile(r"^Atoms.*")

    with open(cfg[DATAS_FILE]) as f:
        for data_file in f.readlines():
            data_file = data_file.strip()
            with open(data_file) as d:
                section = SEC_HEAD
                atom_id = 0
                num_atoms = None
                head_content = []
                atoms_content = []
                tail_content = []
                reorder_data = {}
                for line in d.readlines():
                    line = line.strip()
                    # not currently keeping anything from the header
                    if section == SEC_HEAD:
                        head_content.append(line)
                        if num_atoms is None:
                            atoms_match = num_atoms_pat.match(line)
                            if atoms_match:
                                # regex is 1-based
                                num_atoms = int(atoms_match.group(1))
                        # TODO: do not handle the case if the num atoms is not in the header
                        if atoms_pat.match(line):
                            section = SEC_ATOMS
                            head_content.append('')

                    elif section == SEC_ATOMS:
                        if len(line) == 0:
                            continue
                        atoms_content.append(line)
                        if atom_id in atom_id_dict:
                            reorder_data[atom_id] = line
                        atom_id += 1
                        if len(atoms_content) == num_atoms:
                            section = SEC_TAIL
                    elif section == SEC_TAIL:
                        tail_content.append(line)

            # Now that finished reading the file...
            # Do any necessary reordering
            for atom in reorder_data:
                atoms_content[atom_id_dict[atom]] = reorder_data[atom]


            f_name = create_out_suf_fname(data_file, '_ord', ext='.data')
            list_to_file(head_content+atoms_content+tail_content, f_name)
            print('Completed writing {}'.format(f_name))
    return

def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    # TODO: did not show the expected behavior when I didn't have a required cfg in the ini file
    if ret != GOOD_RET:
        return ret

    # Read template and data files
    cfg = args.config
    try:
        process_data_files(cfg)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading file:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
