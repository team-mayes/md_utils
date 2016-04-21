#!/usr/bin/env python
"""
Reorders a lammps data file
"""

from __future__ import print_function
import ConfigParser
import os
import re
import sys
import argparse

from md_utils.md_common import (list_to_file, InvalidDataError, create_out_fname, warning, process_cfg, read_int_dict,
                                )

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
DATA_FILES = 'data_list_file'
DATA_FILE = 'data_file'
ATOM_ID_DICT_FILE = 'atom_reorder_dict_filename'
ATOM_TYPE_DICT_FILE = 'atom_type_dict_filename'
BOND_TYPE_DICT_FILE = 'bond_type_dict_filename'
ANGL_TYPE_DICT_FILE = 'angle_type_dict_filename'
DIHE_TYPE_DICT_FILE = 'dihedral_type_dict_filename'
IMPR_TYPE_DICT_FILE = 'improper_type_dict_filename'
PRINT_DATA_ATOMS = 'print_interactions_involving_atoms'

PRINT_ATOM_TYPES = 'print_atom_types'
PRINT_BOND_TYPES = 'print_bond_types'
PRINT_ANGLE_TYPES = 'print_angle_types'
PRINT_DIHEDRAL_TYPES = 'print_dihedral_types'
PRINT_IMPROPER_TYPES = 'print_improper_types'

# Defaults
DEF_CFG_FILE = 'data_edit.ini'
# Set notation
DEF_CFG_VALS = {DATA_FILES: 'data_list.txt',
                DATA_FILE: None,
                ATOM_ID_DICT_FILE: None,
                ATOM_TYPE_DICT_FILE: None,
                BOND_TYPE_DICT_FILE: None,
                ANGL_TYPE_DICT_FILE: None,
                DIHE_TYPE_DICT_FILE: None,
                IMPR_TYPE_DICT_FILE: None,
                PRINT_DATA_ATOMS: [],
                PRINT_ATOM_TYPES: [],
                PRINT_BOND_TYPES: [],
                PRINT_ANGLE_TYPES: [],
                PRINT_DIHEDRAL_TYPES: [],
                PRINT_IMPROPER_TYPES: []
                }
REQ_KEYS = {}

# For data template file processing
SEC_HEAD = 'head_section'
SEC_MASSES = 'Masses'
SEC_PAIR_COEFF = 'Pair Coeffs'
SEC_BOND_COEFF = 'Bond Coeffs'
SEC_ANGL_COEFF = 'Angle Coeffs'
SEC_IMPR_COEFF = 'Improper Coeffs'
SEC_DIHE_COEFF = 'Dihedral Coeffs'
SEC_ATOMS = 'Atoms'
SEC_BONDS = 'Bonds'
SEC_ANGLS = 'Angles'
SEC_DIHES = 'Dihedrals'
SEC_IMPRS = 'Impropers'
SEC_VELOS = 'Velocities'

NUM_ATOMS = 'num_atoms'
NUM_BONDS = 'num_bonds'
NUM_ANGLS = 'num_angls'
NUM_DIHES = 'num_dihes'
NUM_IMPRS = 'num_imprs'
NUM_ATOM_TYP = 'num_atom_typ'
NUM_BOND_TYP = 'num_bond_typ'
NUM_ANGL_TYP = 'num_angl_typ'
NUM_DIHE_TYP = 'num_dihe_typ'
NUM_IMPR_TYP = 'num_impr_typ'

# the last entry in the tuple is for the type_dicts key

TYPE_SEC_DICT = {SEC_MASSES: (NUM_ATOM_TYP, PRINT_ATOM_TYPES, SEC_ATOMS),
                 SEC_PAIR_COEFF: (NUM_ATOM_TYP, PRINT_ATOM_TYPES, SEC_ATOMS),
                 SEC_BOND_COEFF: (NUM_BOND_TYP, PRINT_BOND_TYPES, SEC_BONDS),
                 SEC_ANGL_COEFF: (NUM_ANGL_TYP, PRINT_ANGLE_TYPES, SEC_ANGLS),
                 SEC_DIHE_COEFF: (NUM_DIHE_TYP, PRINT_DIHEDRAL_TYPES, SEC_DIHES),
                 SEC_IMPR_COEFF: (NUM_IMPR_TYP, PRINT_IMPROPER_TYPES, SEC_IMPRS),
                 }

# For these sections, keeps track of:
#   * total number of entries
#   * min number of columns per line
NUM_SEC_DICT = {SEC_BONDS: (NUM_BONDS, 4),
                SEC_ANGLS: (NUM_ANGLS, 5),
                SEC_DIHES: (NUM_DIHES, 6),
                SEC_IMPRS: (NUM_IMPRS, 6),
                }

HEADER_PAT_DICT = {NUM_ATOMS: re.compile(r"(\d+).*atoms$"),
                   NUM_BONDS: re.compile(r"(\d+).*bonds$"),
                   NUM_ANGLS: re.compile(r"(\d+).*angles$"),
                   NUM_DIHES: re.compile(r"(\d+).*dihedrals$"),
                   NUM_IMPRS: re.compile(r"(\d+).*impropers$"),
                   NUM_ATOM_TYP: re.compile(r"(\d+).*atom types$"),
                   NUM_BOND_TYP: re.compile(r"(\d+).*bond types$"),
                   NUM_ANGL_TYP: re.compile(r"(\d+).*angle types$"),
                   NUM_DIHE_TYP: re.compile(r"(\d+).*dihedral types$"),
                   NUM_IMPR_TYP: re.compile(r"(\d+).*improper types$"), }

SEC_PAT_DICT = {SEC_MASSES: re.compile(r"^Masses.*"),
                SEC_BOND_COEFF: re.compile(r"^Bond Coe.*"),
                SEC_PAIR_COEFF: re.compile(r"^Pair Coe.*"),
                SEC_ANGL_COEFF: re.compile(r"^Angle Coe.*"),
                SEC_DIHE_COEFF: re.compile(r"^Dihedral Coe.*"),
                SEC_IMPR_COEFF: re.compile(r"^Improper Coe.*"),
                SEC_ATOMS: re.compile(r"^Atoms.*"),
                SEC_VELOS: re.compile(r"^Velocities.*"),
                SEC_BONDS: re.compile(r"^Bonds.*"),
                SEC_ANGLS: re.compile(r"^Angles.*"),
                SEC_DIHES: re.compile(r"^Dihedrals.*"),
                SEC_IMPRS: re.compile(r"^Impropers.*"), }


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
    parser = argparse.ArgumentParser(description='Changes a lammps data file by implementing options such as: '
                                                 'reorder atom ids in a lammps data file, given a dictionary to '
                                                 'reorder the atoms (a csv of old_index,new_index), and/or '
                                                 'change the atom, bond, angle, dihedral, and/or improper types,'
                                                 'given a dictionary to do so. Can also '
                                                 'print info for selected atom ids. ')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format."
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
    except InvalidDataError as e:
        warning(e)
        return args, INVALID_DATA

    return args, GOOD_RET


def find_section_state(line, current_section, section_order, content, highlight_content):
    """
    In addition to finding the current section by matching patterns, resets the count and
    adds to lists that are keeping track of the data being read

    @param line: current line of data file
    @param current_section: current section
    @param section_order: list keeping track of when find an new section
    @param content: dictionary; add a new key for each section found
    @return: the section currently reading, count
    """
    for section, pattern in SEC_PAT_DICT.items():
        if pattern.match(line):
            section_order.append(section)
            content[section] = []
            highlight_content[section] = []
            return section, 1

    if current_section is None:
        raise InvalidDataError("Could not identify section from line: {}".format(line))
    else:
        return current_section, 1


def find_header_values(line, nums_dict):
    """
    Comprehend entries in lammps data file header
    @param line: line in header section
    @param nums_dict: dictionary keep track of total numbers for types (lammps header data)
    @return: updated nums_dict or error
    """
    try:
        for num_key, pattern in HEADER_PAT_DICT.items():
            if nums_dict[num_key] is None:
                pattern_match = pattern.match(line)
                if pattern_match:
                  # regex is 1-based
                    nums_dict[num_key] = int(pattern_match.group(1))
                    return
    except (ValueError, KeyError) as e:
        raise InvalidDataError("While reading a data file, encountered error '{}' on line: {}".format(e, line))


def proc_data_file(cfg, data_file, atom_id_dict, type_dict):
    # Easier to pass when contained in a dictionary
    nums_dict = {}
    num_dict_headers = [NUM_ATOMS, NUM_ATOM_TYP, NUM_BONDS, NUM_BOND_TYP, NUM_ANGLS, NUM_ANGL_TYP,
                        NUM_DIHES, NUM_DIHE_TYP, NUM_IMPRS, NUM_IMPR_TYP]

    with open(data_file) as d:
        print("Reading file: {}".format(data_file))
        section = SEC_HEAD
        section_order = []
        count = 0
        for key in num_dict_headers:
            nums_dict[key] = None
        content = {SEC_HEAD: [], }
        highlight_content = {}

        for line in d.readlines():
            line = line.strip()
            if len(line) == 0:
                continue

            if section is None:
                section, count = find_section_state(line, section, section_order, content, highlight_content)

            elif section == SEC_HEAD:
                # Head is the only section of indeterminate lengths, so check every line *after the first, comment
                # line** to see if a new section is encountered
                if count == 0:
                    content[SEC_HEAD].append(line)
                    content[SEC_HEAD].append('')
                    count += 1
                else:
                    section, count = find_section_state(line, section, section_order, content, highlight_content)
                    if section == SEC_HEAD:
                        content[SEC_HEAD].append(line)
                        find_header_values(line, nums_dict)
                    else:
                        # Upon exiting header, see if have minimum data needed
                        if nums_dict[NUM_ATOMS] is None:
                            raise InvalidDataError("Did not find total atom number in the header of "
                                                   "file {}".format(data_file))

                        for key, val in nums_dict.items():
                            if val <= 0:
                                raise InvalidDataError("Invalid value ({}) encountered for key '{}' in file: "
                                                       "{}".format(val, key, data_file))

            elif section in TYPE_SEC_DICT:
                s_line = line.split()

                try:
                    coeff_id = int(s_line[0])
                except ValueError as e:
                    raise InvalidDataError("Encountered error '{}' reading line: {} \n  in file: "
                                           "{}".format(e, line, data_file))

                # Rename the following to make it easier to follow:
                type_count = TYPE_SEC_DICT[section][0]
                highlight_types = cfg[TYPE_SEC_DICT[section][1]]
                change_dict = type_dict[TYPE_SEC_DICT[section][2]]

                if coeff_id in change_dict:
                    s_line[0] = change_dict[coeff_id]

                content[section].append(s_line)

                if coeff_id in highlight_types:
                    highlight_content[section].append(line)
                if type_count in nums_dict:
                    if count == nums_dict[type_count]:
                        section = None
                    else:
                        count += 1
                else:
                    raise InvalidDataError("Found section {}, but did not find number of entries for that section "
                                           "in the header.".format(section))

            elif section in [SEC_ATOMS, SEC_VELOS]:
                s_line = line.split()
                try:
                    atom_id = int(s_line[0])
                    atom_type = int(s_line[2])
                except (ValueError, KeyError) as e:
                    raise InvalidDataError("Error {} on line: {}\n  in file: {}".format(e, line, data_file))

                if atom_id in atom_id_dict:
                    s_line[0] = atom_id_dict[atom_id]
                else:
                    s_line[0] = atom_id

                if atom_type in type_dict[SEC_ATOMS]:
                    s_line[2] = type_dict[SEC_ATOMS][atom_type]

                content[section].append(s_line)

                if atom_id in cfg[PRINT_DATA_ATOMS]:
                    highlight_content[section].append(s_line)

                if count == nums_dict[NUM_ATOMS]:
                    content[section].sort()
                    highlight_content[section].sort()
                    section = None
                else:
                    count += 1
            elif section in NUM_SEC_DICT:
                highlight_line = False
                tot_num_key = NUM_SEC_DICT[section][0]
                if tot_num_key not in nums_dict:
                    raise InvalidDataError("Found section {}, but did not find number of bonds "
                                           "in the header.".format(section))

                min_col_num = NUM_SEC_DICT[section][1]
                s_line = line.split()
                try:
                    sec_type = int(s_line[1])
                    atoms = map(int, s_line[2:min_col_num])
                except (ValueError, KeyError) as e:
                    raise InvalidDataError("Error {} reading line: {} \n  in section {} of file: {} "
                                           "".format(e, line, section, data_file))
                new_atoms = atoms
                for index, atom_id in enumerate(atoms):
                    if atom_id in atom_id_dict:
                        new_atoms[index] = atom_id_dict[atom_id]
                    if atom_id in cfg[PRINT_DATA_ATOMS]:
                        highlight_line = True

                if sec_type in type_dict[section]:
                    s_line[1] = type_dict[section][sec_type]

                if len(s_line) > min_col_num:
                    end = s_line[min_col_num:]
                else:
                    end = []

                line_struct = s_line[0:2] + new_atoms + end
                content[section].append(line_struct)

                if highlight_line:
                    highlight_content[section].append(line_struct)

                if count == nums_dict[tot_num_key]:
                    section = None
                else:
                    count += 1

            else:
                warning("Note: unexpected content added to end of file:", line)

    data_content = content[SEC_HEAD]
    select_data_content = []
    for section in section_order:
        # empty list will become an empty line
        data_content += [''] + [section, ''] + content[section]
        select_data_content += [section] + highlight_content[section]

    # Only print a "new" data file if something is changed
    dict_lens = len(atom_id_dict)
    for name, t_dict in type_dict.items():
        dict_lens += len(t_dict)

    if dict_lens > 0:
        f_name = create_out_fname(data_file, suffix='_new', ext='.data')
        list_to_file(data_content, f_name)
        print('Completed writing {}'.format(f_name))

    if len(cfg[PRINT_DATA_ATOMS]) > 0:
        f_name = create_out_fname(data_file, suffix='_selected', ext='.txt')
        list_to_file(select_data_content, f_name)
        print('Completed writing {}'.format(f_name))


def process_data_files(cfg, atom_id_dict, type_dicts):
    if os.path.isfile(cfg[DATA_FILES]):
        with open(cfg[DATA_FILES]) as f:
            for data_file in f.readlines():
                data_file = data_file.strip()
                if len(data_file) == 0:
                    continue
                proc_data_file(cfg, data_file, atom_id_dict, type_dicts,)
    if cfg[DATA_FILE] is not None:
        proc_data_file(cfg, cfg[DATA_FILE], atom_id_dict, type_dicts,)


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    # Read template and data files
    cfg = args.config

    if cfg[DATA_FILE] is None:
        if not(os.path.isfile(cfg[DATA_FILES])):
            warning("Did not find a list of data files at the path: {}\n"
                    "In the configuration file, specify a location of a single data file with the keyword {}\n"
                    "and/or a single data file with the keyword {}".format(cfg[DATA_FILES], DATA_FILES, DATA_FILE))
            return INVALID_DATA

    type_dicts = {SEC_ATOMS: {},
                  SEC_BONDS: {},
                  SEC_ANGLS: {},
                  SEC_DIHES: {},
                  SEC_IMPRS: {}, }

    try:
        atom_id_dict = read_int_dict(cfg[ATOM_ID_DICT_FILE], one_to_one=False)
        type_dicts[SEC_ATOMS] = read_int_dict(cfg[ATOM_TYPE_DICT_FILE], one_to_one=False)
        type_dicts[SEC_BONDS] = read_int_dict(cfg[BOND_TYPE_DICT_FILE], one_to_one=False)
        type_dicts[SEC_ANGLS] = read_int_dict(cfg[ANGL_TYPE_DICT_FILE], one_to_one=False)
        type_dicts[SEC_DIHES] = read_int_dict(cfg[DIHE_TYPE_DICT_FILE], one_to_one=False)
        type_dicts[SEC_IMPRS] = read_int_dict(cfg[IMPR_TYPE_DICT_FILE], one_to_one=False)
        process_data_files(cfg, atom_id_dict, type_dicts)
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
