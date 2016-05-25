#!/usr/bin/env python
"""
Get selected info from the file
"""

from __future__ import print_function
# noinspection PyCompatibility
import ConfigParser
import logging
import re
import sys
import argparse

from md_utils.md_common import InvalidDataError, warning, process_cfg


__author__ = 'hmayes'


# Logging
logger = logging.getLogger('cp2k_get_info')
logging.basicConfig(filename='cp2k_get_info.log', filemode='w', level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)


# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3

# Constants #
TOL = 0.000001

# Config File Sections
MAIN_SEC = 'main'

# Config keys
CHK_FILE = 'cp2k_file'
DATA_FILE = 'data_file'


# Defaults
DEF_CFG_FILE = 'cp2k_get_info.ini'
# Set notation
DEF_CFG_VALS = {}
REQ_KEYS = {CHK_FILE: str, DATA_FILE: str, }

# Sections
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_CHARGES = 'mm_charge_section'
SEC_TAIL = 'tail_section'

# Content
NUM_ATOMS = 'num_atoms'
HEAD_CONTENT = 'head_content'
MM_CHARGES = 'mm_atom_charges'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'


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
    parser = argparse.ArgumentParser(description='Grabs selected info from the designated file. '
                                                 'The required input file provides the location of the file. '
                                                 'Optional info is an atom index for the last atom not to consider.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
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


def process_data_file(cfg):
    tpl_loc = cfg[DATA_FILE]
    num_atoms = None
    atoms_content = []
    section = SEC_HEAD
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    atoms_pat = re.compile(r"^Atoms.*")

    total_charge = 0.0

    # For debugging total charge
    key_atom_ids = {'last_p1': 15436, 15436: 'last_p1', 16327: 'last_p2', 16328: 'lone_pot', 65640: 'last_lipid',
                    65644: 'last_hyd', 213877: 'last_water', 213992: 'last_pot'}

    with open(tpl_loc) as f:
        for line in f:
            line = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                if num_atoms is None:
                    atoms_match = num_atoms_pat.match(line)
                    if atoms_match:
                        # regex is 1-based
                        num_atoms = int(atoms_match.group(1))
                if atoms_pat.match(line):
                    section = SEC_ATOMS
            # atoms_content to contain everything but the xyz: atom_num, mol_num, atom_type, charge, type'
            elif section == SEC_ATOMS:
                split_line = line.split()
                if len(split_line) == 0:
                    continue
                elif len(split_line) < 7:
                    break
                atom_num = int(split_line[0])
                mol_num = int(split_line[1])
                atom_type = int(split_line[2])
                charge = float(split_line[3])
                try:
                    atom_descrip = split_line[8]
                except IndexError:
                    atom_descrip = ''
                atom_struct = [atom_num, mol_num, atom_type, charge, atom_descrip]
                atoms_content.append(atom_struct)
                total_charge += charge

                if atom_num == num_atoms:
                    section = SEC_TAIL
                    # Also check total charge
                    print('Total charge is: {}'.format(total_charge))
                elif atom_num in key_atom_ids:
                    print('After atom {} ({}), the total charge is: {}'.format(atom_num, key_atom_ids[atom_num],
                                                                               total_charge))

            elif section == SEC_TAIL:
                break

    # Validate data section
    if len(atoms_content) != num_atoms:
        raise InvalidDataError('The length of the "Atoms" section ({}) does not equal '
                               'the number of atoms ({}).'.format(len(atoms_content), num_atoms))

    return atoms_content, num_atoms


def process_cp2k_out_file(cfg, num_atoms):

    cp2k_loc = cfg[CHK_FILE]
    mm_charge_data = []

    section = SEC_HEAD
    mm_charge_pat = re.compile(r".*MM    POINT CHARGES.*")
    section_line_pat = re.compile(r".*----.*")
    col_ignore = 22
    atom_num = 0
    ignore_line = True

    with open(cp2k_loc) as f:
        for line in f:
            line = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                mm_charge_match = mm_charge_pat.match(line)
                if mm_charge_match:
                    section = SEC_CHARGES

            elif section == SEC_CHARGES:
                skip_line_match = section_line_pat.match(line)
                if len(line) == 0:
                    continue
                if skip_line_match:
                    if ignore_line:
                        ignore_line = False
                        continue
                    else:
                        # Got to the next section
                        print('Finished section after reading {} mm atoms, which is less than the '
                              '{} atoms in the data file.'.format(len(mm_charge_data), num_atoms))
                        # raise InvalidDataError('Finished section after reading {} mm atoms, which is less than the '
                        #                        '{} atoms in the data file.'.format(len(mm_charge_data), num_atoms))
                        break

                line_end = line[col_ignore:-1]
                split_line = line_end.split()
                atom_num += 1
                radius = float(split_line[0])
                charge = float(split_line[2])

                atom_struct = [atom_num, radius, charge]
                mm_charge_data.append(atom_struct)

                if len(mm_charge_data) == num_atoms:
                    section = SEC_TAIL
            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                break

    return mm_charge_data


def compare_data(data_atoms, mm_charge_data):
    for atom_id, entry in enumerate(mm_charge_data):
        if atom_id < 3:
            print(data_atoms[atom_id], entry)
        if abs(data_atoms[atom_id][3] - entry[2]) > TOL:
            print('Check me out! {} vs {}'.format(data_atoms[atom_id], entry))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    # TODO: did not show the expected behavior when I didn't have a required cfg in the ini file
    if ret != GOOD_RET:
        return ret

    # Read template and data files
    cfg = args.config

    try:
        data_atoms_content, num_atoms = process_data_file(cfg)
        mm_charge_data = process_cp2k_out_file(cfg, num_atoms)
        compare_data(data_atoms_content, mm_charge_data)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data template:", e)
        return INVALID_DATA

    # print(psf_data_content[ATOMS_CONTENT])

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
