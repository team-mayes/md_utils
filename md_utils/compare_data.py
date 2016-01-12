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
logger = logging.getLogger('data2pdb')
logging.basicConfig(filename='data2pdb.log', filemode='w', level=logging.DEBUG)
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
# DATA_TPL_FILE = 'data_tpl_file'
DATAS_FILE = 'data_list_file'
# ATOM_TYPE_DICT_FILE = 'atom_type_dict_filename'

# data file info


# Defaults
DEF_CFG_FILE = 'compare_data.ini'
# Set notation
DEF_CFG_VALS = {DATAS_FILE: 'data_list.txt',
}
REQ_KEYS = {
}

# From data template file
NUM_ATOMS = 'num_atoms'
HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'
ATOM_TYPE_DICT = 'atom_type_dict'
ATOM_ID_DICT = 'atom_id_dict'

# For data template file processing
SEC_HEAD = 'head_section'
SEC_MASSES = 'masses_section'
SEC_PAIR_COEFF = 'pair_coeff_section'
SEC_ANGL_COEFF = 'angle_coeff_section'
SEC_IMPR_COEFF = 'improp_coeff_section'
SEC_DIHE_COEFF = 'dihe_coeff_section'
SEC_ATOMS = 'atoms_section'
SEC_BONDS = 'bonds_section'
SEC_ANGLS = 'angles_section'
SEC_DIHES = 'dihedrals_section'
SEC_IMPRS = 'impropers_section'
SEC_VELOS = 'velos_section'

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
    parser = argparse.ArgumentParser(description='Compares parts of data files to determine differences.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini "
                                               "format. See the example file /test/test_data/evbd2d/compare_data.ini. "
                                               "The default file name is compare_data.ini, located in the "
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


def print_data(head, data, tail, f_name):
    list_to_file(head, f_name)
    seq_list_to_file(data, f_name, mode='a')
    list_to_file(tail, f_name, mode='a')
    return

def find_section_state(line, current_section):
    masses_pat = re.compile(r"^Masses.*")
    pair_pat = re.compile(r"^Pair Coe.*")
    angl_pat = re.compile(r"^Angle Coe.*")
    dihe_pat = re.compile(r"^Dihedral Coe.*")
    impr_pat = re.compile(r"^Improper Coe.*")
    atoms_pat = re.compile(r"^Atoms.*")
    velos_pat = re.compile(r"^Velocities.*")
    bonds_pat = re.compile(r"^Bonds.*")
    angls_pat = re.compile(r"^Angles.*")
    dihes_pat = re.compile(r"^Dihedrals.*")
    imprs_pat = re.compile(r"^Impropers.*")
    if masses_pat.match(line):
        return SEC_MASSES
    elif pair_pat.match(line):
        return SEC_PAIR_COEFF 
    elif angl_pat.match(line):
        return SEC_ANGL_COEFF
    elif dihe_pat.match(line):
        return SEC_DIHE_COEFF
    elif impr_pat.match(line):
        return SEC_IMPR_COEFF
    elif atoms_pat.match(line):
        return SEC_ATOMS
    elif velos_pat.match(line):
        return SEC_VELOS
    elif bonds_pat.match(line):
        return SEC_BONDS
    elif angls_pat.match(line):
        return SEC_ANGLS
    elif dihes_pat.match(line):
        return SEC_DIHES
    elif imprs_pat.match(line):
        return SEC_IMPRS
    else:
        return current_section


def process_data_files(cfg):

    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    num_bonds_pat = re.compile(r"(\d+).*bonds$")
    num_angl_pat = re.compile(r"(\d+).*angles$")
    num_dihe_pat = re.compile(r"(\d+).*dihedrals$")
    num_impr_pat = re.compile(r"(\d+).*impropers$")

    num_atom_typ_pat = re.compile(r"(\d+).*atom types$")
    num_bond_typ_pat = re.compile(r"(\d+).*bond types$")
    num_angl_typ_pat = re.compile(r"(\d+).*angle types$")
    num_dihe_typ_pat = re.compile(r"(\d+).*dihedral types$")
    num_impr_typ_pat = re.compile(r"(\d+).*improper types$")

    # Create dictionaries
    masses = {}
    atoms = {}
    pairs = {}

    first_file = True
    with open(cfg[DATAS_FILE]) as f:
        for data_file in f.readlines():
            data_file = data_file.strip()
            with open(data_file) as d:
                section = SEC_HEAD
                num_atoms = None
                num_bonds = None
                num_angls = None
                num_dihes = None
                num_imprs = None
                num_atom_typ = None
                num_bond_typ = None
                num_angl_typ = None
                num_dihe_typ = None
                num_impr_typ = None
                count = 0
                for line in d.readlines():
                    line = line.strip()
                    if len(line) == 0:
                        continue
                    if section is None:
                        section = find_section_state(line, section)
                        count = 0
                        continue
                    elif section == SEC_HEAD:
                        section = find_section_state(line, section)
                        if section != SEC_HEAD:
                            # TODO: check if any of the numbers are missing
                            continue
                        if num_atoms is None:
                            atoms_match = num_atoms_pat.match(line)
                            if atoms_match:
                                # regex is 1-based
                                num_atoms = int(atoms_match.group(1))
                        if num_atom_typ is None:
                            atom_match = num_atom_typ_pat.match(line)
                            if atom_match:
                                # regex is 1-based
                                num_atom_typ = int(atom_match.group(1))
                        if num_bonds is None:
                            bonds_match = num_bonds_pat.match(line)
                            if bonds_match:
                                # regex is 1-based
                                num_bonds = int(bonds_match.group(1))
                        if num_bond_typ is None:
                            bond_match = num_bond_typ_pat.match(line)
                            if bond_match:
                                # regex is 1-based
                                num_bond_typ = int(bond_match.group(1))
                        if num_angls is None:
                            angls_match = num_angl_pat.match(line)
                            if angls_match:
                                # regex is 1-based
                                num_angls = int(angls_match.group(1))
                        if num_angl_typ is None:
                            angl_match = num_angl_typ_pat.match(line)
                            if angl_match:
                                # regex is 1-based
                                num_angl_typ = int(angl_match.group(1))
                        if num_dihes is None:
                            dihes_match = num_dihe_pat.match(line)
                            if dihes_match:
                                # regex is 1-based
                                num_dihes = int(dihes_match.group(1))
                        if num_dihe_typ is None:
                            dihe_match = num_dihe_typ_pat.match(line)
                            if dihe_match:
                                # regex is 1-based
                                num_dihe_typ = int(dihe_match.group(1))
                        if num_imprs is None:
                            imprs_match = num_impr_pat.match(line)
                            if imprs_match:
                                # regex is 1-based
                                num_imprs = int(imprs_match.group(1))
                        if num_impr_typ is None:
                            impr_match = num_impr_typ_pat.match(line)
                            if impr_match:
                                # regex is 1-based
                                num_impr_typ = int(impr_match.group(1))
                    elif section == SEC_MASSES:
                        count += 1
                        split_line = line.split()
                        if first_file:
                            masses[split_line[0]] = split_line[1]
                        else:
                            if split_line[0] in masses:
                                if masses[split_line[0]] == split_line[1]:
                                    continue
                                else:
                                    print('Error: masses to not match for line: ', line)
                                    print(masses[split_line[0]],split_line[1])
                                    break
                            else:
                                print('Key for this line does not match first file:', line)
                        # Check after increment because the counter started at 0
                        if count == num_atom_typ:
                            print('Completed reading',section)
                            section = None
                    elif section == SEC_PAIR_COEFF:
                        count += 1
                        split_line = line.split()
                        pairs[split_line[0]] = split_line[1:]
                        # Check after increment because the counter started at 0
                        if count == num_atom_typ:
                            section = None
                    elif section == SEC_ATOMS:
                        count += 1
                        split_line = line.split()
                        atoms[split_line[0]] = split_line[1:]
                        # Check after increment because the counter started at 0
                        if count == num_atoms:
                            section = None


#  = 'pair_coeff_section'
# SEC_ANGL_COEFF = 'angle_coeff_section'
# SEC_IMPR_COEFF = 'improp_coeff_section'
# SEC_DIHE_COEFF = 'dihe_coeff_section'
# SEC_ATOMS = 'atoms_section'
# SEC_BONDS = 'bonds_section'
# SEC_ANGLS = 'angles_section'
# SEC_DIHES = 'dihedrals_section'
# SEC_IMPRS = 'impropers_section'
# SEC_VELOS = 'velos_section'

            first_file = False
            print(num_atoms, num_bonds, num_angls, num_dihes, num_imprs)
            # Now make new file
            # f_name = create_out_suf_fname(data_file, '_new', ext='.data')
            # print_data(data_tpl_content[HEAD_CONTENT], new_data_section, data_tpl_content[TAIL_CONTENT],
            #            f_name)
            # print('Completed writing {}'.format(f_name))

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
        warning("Problems reading data template:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
