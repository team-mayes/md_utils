#!/usr/bin/env python
from __future__ import print_function

import ConfigParser
import logging
import re
from md_utils.md_common import NotFoundError, list_to_file, InvalidDataError, seq_list_to_file

NUM_ATOMS = 'num_atoms'

TAIL_CONTENT = 'tail_content'

ATOMS_CONTENT = 'atoms_content'

HEAD_CONTENT = 'head_content'

SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'

"""
Creates lammps data files from lammps dump files, given a template lammps data file.
"""

import sys
import argparse

__author__ = 'mayes'


# Logging
logging.basicConfig(filename='evbd2d.log', level=logging.DEBUG, filemode='w')
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('evbd2d')


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
DATA_TPL_FILE = 'data_tpl_file'
DUMPS_FILE = 'dump_list_file'
WAT_O = 'water_o_type'
WAT_H = 'water_o_type'
H3O_O = 'h3o_o_type'
H3O_H = 'h3o_h_type'
PROT_RES = 'prot_res'
PROT_H = 'prot_h_type'
PROT_IGNORE = 'prot_ignore_atom_nums'

# Defaults
DEF_CFG_FILE = 'evbd2d.ini'
# Set notation
DEF_CFG_VALS = {DUMPS_FILE: 'dump_list.txt', PROT_IGNORE: [], }
DEF_REQ_KEYS = [DATA_TPL_FILE, WAT_O, WAT_H, H3O_O, H3O_H, PROT_RES, PROT_H, ]

def warning(*objs):
    """Writes a message to stderr."""
    print("WARNING: ", *objs, file=sys.stderr)

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
        return list(param)
    return param

def process_cfg(raw_cfg):
    """
    Converts the given raw configuration, filling in defaults and converting the specified value (if any) to the
    default value's type.
    :param raw_cfg: The configuration map.
    :return: The processed configuration.
    """
    proc_cfg = {}
    for key, def_val in DEF_CFG_VALS.items():
        proc_cfg[key] = conv_raw_val(raw_cfg.get(key), def_val)

    for key in DEF_REQ_KEYS:
        proc_cfg[key] = conv_raw_val(raw_cfg.get(key), None)
        if proc_cfg[key] is None:
            raise NotFoundError('Input value for {} missing in the configuration file.'.format(key))

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
    # TODO: Add description
    parser = argparse.ArgumentParser(description='Creates lammps data files from lammps dump files, given a template '
                                                 'lammps data file. The required input file provides the location of the '
                                                 'data template file, a file with a list of dump files to convert, and'
                                                 'information about the configuration of the data file, needed to '
                                                 'process the dump file to produce data files matching the template '
                                                 '(consistent ID for the hydronium ion, protonatable residue always'
                                                 'deprotonated, etc.). Currently, this script expects only one '
                                                 'protonatable residue.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini "
                                               "format. See the example file /test/test_data/markovian.ini. "
                                               "The default file name is markovian.ini, located in the "
                                               "base directory where the program as run.",
                        default=DEF_CFG_FILE, type=read_cfg)
    # parser.add_argument("-i", "--input_rates", help="The location of the input rates file",
    #                     default=DEF_IRATE_FILE, type=read_input_rates)
    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except NotFoundError as e:
        warning("Input data missing:", e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def process_data_tpl(tpl_loc):
    tpl_data = {}
    tpl_data[HEAD_CONTENT] = []
    tpl_data[ATOMS_CONTENT] = []
    tpl_data[TAIL_CONTENT] = []
    section = SEC_HEAD
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    atoms_pat = re.compile(r"^Atoms.*")
    velos_pat = re.compile(r"^Velocities.*")
    with open(tpl_loc) as f:
        for line in f.readlines():
            line = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                tpl_data[HEAD_CONTENT].append(line)
                if NUM_ATOMS not in tpl_data:
                    atoms_match = num_atoms_pat.match(line)
                    if atoms_match:
                        # regex is 1-based
                        tpl_data[NUM_ATOMS] = int(atoms_match.group(1))
                if atoms_pat.match(line):
                    section = SEC_ATOMS
                    tpl_data[HEAD_CONTENT].append('')
            # atoms_content to contain everything but the xyz: atom_num, mol_num, atom_type, charge'
            elif section == SEC_ATOMS:
                if len(line)==0:
                    continue
                if velos_pat.match(line):
                    section = SEC_TAIL
                    # Append one new line
                    tpl_data[TAIL_CONTENT].append('')
                    tpl_data[TAIL_CONTENT].append(line)
                    continue
                split_line = line.split()
                atom_num = int(split_line[0])
                mol_num = int(split_line[1])
                atom_type = int(split_line[2])
                charge = float(split_line[3])
                tpl_data[ATOMS_CONTENT].append((atom_num, mol_num, atom_type, charge))
            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                tpl_data[TAIL_CONTENT].append(line)

    # Validate data section
    if len(tpl_data[ATOMS_CONTENT]) != tpl_data[NUM_ATOMS]:
        raise InvalidDataError('The length of the "Atoms" section ({}) does not equal the' \
                               'number of atoms ({}).'.format(len(tpl_data[ATOMS_CONTENT]),tpl_data[NUM_ATOMS]))

    if logger.isEnabledFor(logging.DEBUG):
        list_to_file(tpl_data[HEAD_CONTENT],'head.txt')
        seq_list_to_file(tpl_data[ATOMS_CONTENT],'atoms.txt')
        list_to_file(tpl_data[TAIL_CONTENT],'tail.txt')

    return tpl_data


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    # Read template file
    cfg = args.config
    try:
        content = process_data_tpl(cfg[DATA_TPL_FILE])
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
