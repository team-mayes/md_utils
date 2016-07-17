#!/usr/bin/env python
"""
Reorders a lammps data file
"""

from __future__ import print_function
# noinspection PyCompatibility
import ConfigParser
from operator import itemgetter
import os
import re
import sys
import argparse

from md_utils.md_common import (list_to_file, InvalidDataError, create_out_fname, warning, process_cfg, read_int_dict)

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
DATA_COMP = 'data_comp_file'
ATOM_ID_DICT_FILE = 'atom_reorder_dict_filename'
ATOM_TYPE_DICT_FILE = 'atom_type_dict_filename'
BOND_TYPE_DICT_FILE = 'bond_type_dict_filename'
ANGL_TYPE_DICT_FILE = 'angle_type_dict_filename'
DIHE_TYPE_DICT_FILE = 'dihedral_type_dict_filename'
IMPR_TYPE_DICT_FILE = 'improper_type_dict_filename'
PRINT_OWN_ATOMS = 'print_interactions_owned_by_atoms'
PRINT_DATA_ATOMS = 'print_interactions_involving_atoms'
SORT_ME = 'data_sort_flag'

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
                DATA_COMP: None,
                ATOM_ID_DICT_FILE: None,
                ATOM_TYPE_DICT_FILE: None,
                BOND_TYPE_DICT_FILE: None,
                ANGL_TYPE_DICT_FILE: None,
                DIHE_TYPE_DICT_FILE: None,
                IMPR_TYPE_DICT_FILE: None,
                PRINT_OWN_ATOMS: [],
                PRINT_DATA_ATOMS: [],
                PRINT_ATOM_TYPES: [],
                PRINT_BOND_TYPES: [],
                PRINT_ANGLE_TYPES: [],
                PRINT_DIHEDRAL_TYPES: [],
                PRINT_IMPROPER_TYPES: [],
                SORT_ME: False,
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
# For these sections, keeps track of:
#   * total number of entries
#   * list of types to print
#   * dictionary of any changes to make
TYPE_SEC_DICT = {SEC_MASSES: (NUM_ATOM_TYP, PRINT_ATOM_TYPES, SEC_ATOMS),
                 SEC_PAIR_COEFF: (NUM_ATOM_TYP, PRINT_ATOM_TYPES, SEC_ATOMS),
                 SEC_BOND_COEFF: (NUM_BOND_TYP, PRINT_BOND_TYPES, SEC_BONDS),
                 SEC_ANGL_COEFF: (NUM_ANGL_TYP, PRINT_ANGLE_TYPES, SEC_ANGLS),
                 SEC_DIHE_COEFF: (NUM_DIHE_TYP, PRINT_DIHEDRAL_TYPES, SEC_DIHES),
                 SEC_IMPR_COEFF: (NUM_IMPR_TYP, PRINT_IMPROPER_TYPES, SEC_IMPRS),
                 }

SEC_FORMAT_DICT = {SEC_ATOMS: ("{:8d} {:>7} {:>5} {:>9.2f} {:>11.3f} {:>11.3f} {:>11.3f}  ", 7),
                   SEC_MASSES: ("{:8d} {:>10}  ", 2),
                   SEC_PAIR_COEFF: ("{:8d} {:>10} {:>10} {:>10} {:>10}  ", 5),
                   SEC_BOND_COEFF: ("{:8d} {:>10} {:>10}  ", 3),
                   SEC_ANGL_COEFF: ("{:>8} {:>10} {:>10} {:>10} {:>10}  ", 5),
                   SEC_DIHE_COEFF: ("{:>8} {:>10} {:>10} {:>10} {:>10}  ", 5),
                   SEC_IMPR_COEFF: ("{:8d} {:>10} {:>10}  ", 3),
                   SEC_BONDS: ("{:>8} {:>7} {:>7} {:>7}  ", 4),
                   SEC_ANGLS: ("{:>8} {:>7} {:>7} {:>7} {:>7}  ", 5),
                   SEC_DIHES: ("{:>8} {:>7} {:>7} {:>7} {:>7} {:>7}  ", 6),
                   SEC_IMPRS: ("{:>8} {:>7} {:>7} {:>7} {:>7} {:>7}  ", 6),
                   SEC_VELOS: ("{:>8} {:>11.5f} {:>11.5f} {:>11.5f}  ", 4),
                   }
# {:8d} {:>10}  {:}".format(s_line[0], s_line[1], " ".join(s_line[2:]

#  number of columns for comparison, for sections in which order is maintained
COMP_ORD_SEC_COL_DICT = {SEC_ATOMS: 4,
                         SEC_MASSES: 2,
                         SEC_PAIR_COEFF: 5,
                         SEC_BOND_COEFF: 3,
                         SEC_ANGL_COEFF: 5,
                         SEC_DIHE_COEFF: 5,
                         SEC_IMPR_COEFF: 3,
                         }

# For these sections, keep track of:
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

# For output from comparing data files; how indicate it came from the first file or second
FILE1_SIGN = "+ "
FILE2_SIGN = "- "
# tolerance for comparing output files
COMP_TOL = 0.00001


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
    # except KeyError as e:
    #     warning("Input data missing:", e)
    #     parser.print_help()
    #     return args, INPUT_ERROR
    except InvalidDataError as e:
        warning(e)
        return args, INVALID_DATA
    except ConfigParser.MissingSectionHeaderError as e:
        warning(e)
        return args, INPUT_ERROR

    return args, GOOD_RET


def find_section_state(line, current_section, section_order, content, highlight_content):
    """
    In addition to finding the current section by matching patterns, resets the count and
    adds to lists that are keeping track of the data being read

    @param line: current line of data file
    @param current_section: current section
    @param section_order: list keeping track of when find an new section
    @param content: dictionary; add a new key for each section found
    @param highlight_content: keep a list of selected content to output (interactions with specified atoms)
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
    """
    Reads each section and gathers data for various options
    @param cfg:
    @param data_file:
    @param atom_id_dict:
    @param type_dict:
    @return:
    """
    # Easier to pass when contained in a dictionary
    nums_dict = {}
    num_dict_headers = [NUM_ATOMS, NUM_ATOM_TYP, NUM_BONDS, NUM_BOND_TYP, NUM_ANGLS, NUM_ANGL_TYP,
                        NUM_DIHES, NUM_DIHE_TYP, NUM_IMPRS, NUM_IMPR_TYP]

    with open(data_file) as d:
        print("Reading file: {}".format(data_file))
        section = SEC_HEAD
        found_box_size = False
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
                        s_line = line.split()
                        try:
                            # For the box sizes:
                            s_line[0:2] = map(float, s_line[0:2])
                            if not found_box_size:
                                found_box_size = True
                                content[SEC_HEAD].append("")
                            content[SEC_HEAD].append('{:12.5f} {:12.5f} {:} {:}'.format(*s_line))
                        except ValueError:
                            s_line[0] = int(s_line[0])
                            content[SEC_HEAD].append('{:12d}  {:}'.format(s_line[0], " ".join(s_line[1:])))
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
                    raise InvalidDataError("Encountered error '{}' reading line: {} \n  in file: {}\n"
                                           "Check number of lines in the section to make sure that they match the "
                                           "number specified in the header section.".format(e, line, data_file))

                # Rename the following to make it easier to follow:
                type_count = TYPE_SEC_DICT[section][0]
                highlight_types = cfg[TYPE_SEC_DICT[section][1]]
                change_dict = type_dict[TYPE_SEC_DICT[section][2]]

                if coeff_id in change_dict:
                    s_line[0] = change_dict[coeff_id]
                else:
                    s_line[0] = coeff_id

                content[section].append(s_line)

                if coeff_id in highlight_types:
                    highlight_content[section].append(s_line)
                if type_count in nums_dict:
                    if count == nums_dict[type_count]:
                        content[section].sort()
                        section = None

                    else:
                        count += 1
                else:
                    raise InvalidDataError("Found section {}, but did not find number of entries for that section "
                                           "in the header.".format(section))

            elif section == SEC_VELOS:
                s_line = line.split()
                try:
                    atom_id = int(s_line[0])
                except (ValueError, KeyError) as e:
                    raise InvalidDataError("In section '{}', Error {} on line: {}\n  in file: {}"
                                           "".format(section, e, line, data_file))
                if atom_id in atom_id_dict:
                    s_line[0] = atom_id_dict[atom_id]
                else:
                    s_line[0] = atom_id
                content[section].append(s_line)

                if atom_id in cfg[PRINT_DATA_ATOMS] or atom_id in cfg[PRINT_OWN_ATOMS]:
                    highlight_content[section].append(s_line)

                for col in range(1, 4):
                    s_line[col] = float(s_line[col])

                if count == nums_dict[NUM_ATOMS]:
                    content[section].sort()
                    highlight_content[section].sort()
                    section = None
                else:
                    count += 1

            elif section == SEC_ATOMS:
                s_line = line.split()
                try:
                    atom_id = int(s_line[0])
                    atom_type = int(s_line[2])
                except (ValueError, KeyError) as e:
                    raise InvalidDataError("In section '{}', Error {} on line: {}\n  in file: {}"
                                           "".format(section, e, line, data_file))

                if atom_id in atom_id_dict:
                    s_line[0] = atom_id_dict[atom_id]
                else:
                    s_line[0] = atom_id

                if atom_type in type_dict[SEC_ATOMS]:
                    s_line[2] = type_dict[SEC_ATOMS][atom_type]

                for col in range(3, 7):
                    s_line[col] = float(s_line[col])

                content[section].append(s_line)

                if atom_id in cfg[PRINT_DATA_ATOMS] or atom_id in cfg[PRINT_OWN_ATOMS]:
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
                    s_line[0] = int(s_line[0])
                    s_line[1] = int(s_line[1])
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

                # check for ownership
                if section == SEC_BONDS:
                    if atoms[0] in cfg[PRINT_OWN_ATOMS]:
                        highlight_line = True
                else:
                    if atoms[1] in cfg[PRINT_OWN_ATOMS]:
                        highlight_line = True

                if s_line[1] in type_dict[section]:
                    s_line[1] = type_dict[section][s_line[1]]

                if len(s_line) > min_col_num:
                    end = s_line[min_col_num:]
                else:
                    end = []

                # noinspection PyTypeChecker
                line_struct = s_line[0:2] + new_atoms + end
                content[section].append(line_struct)

                if highlight_line:
                    highlight_content[section].append(line_struct)

                if count == nums_dict[tot_num_key]:
                    if cfg[SORT_ME]:
                        if section == SEC_BONDS:
                            content[section].sort(key=itemgetter(3))
                            content[section].sort(key=itemgetter(2))
                        elif section == SEC_ANGLS:
                            content[section].sort(key=itemgetter(4))
                            content[section].sort(key=itemgetter(2))
                            content[section].sort(key=itemgetter(3))
                        else:
                            content[section].sort(key=itemgetter(5))
                            content[section].sort(key=itemgetter(4))
                            content[section].sort(key=itemgetter(2))
                            content[section].sort(key=itemgetter(3))
                        # noinspection PyAssignmentToLoopOrWithParameter
                        for index, line in enumerate(content[section]):
                            line[0] = index + 1
                    section = None
                else:
                    count += 1

    if cfg[DATA_COMP] is None:
        print_content(atom_id_dict, cfg, content, data_file, highlight_content, section_order, type_dict)
        return
    else:
        return content, section_order


def print_content(atom_id_dict, cfg, content, data_file, highlight_content, section_order, type_dict):
    data_content = content[SEC_HEAD]
    select_data_content = []
    for section in section_order:
        # empty list will become an empty line
        data_content += [''] + [section, '']
        select_data_content += [section]
        sec_format = SEC_FORMAT_DICT[section][0]
        comment_col = SEC_FORMAT_DICT[section][1]
        for line in content[section]:
            data_content.append(sec_format.format(*line[:comment_col]) + " ".join(line[comment_col:]))
        for line in highlight_content[section]:
            select_data_content.append(sec_format.format(*line[:comment_col]) + " ".join(line[comment_col:]))

    # Only print a "new" data file if something is changed
    dict_lens = len(atom_id_dict)
    for name, t_dict in type_dict.items():
        dict_lens += len(t_dict)
    if dict_lens > 0 or cfg[SORT_ME]:
        f_name = create_out_fname(data_file, suffix='_new', ext='.data')
        list_to_file(data_content, f_name)
        print('Completed writing {}'.format(f_name))
    if (len(cfg[PRINT_DATA_ATOMS]) + len(cfg[PRINT_OWN_ATOMS])) > 0:
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


def compare_heads(list1, list2, diff_list):
    """
    Convert a list to a dictionary and see how they are different
    @param list1: list of strings
    @param list2: second list of strings
    @param diff_list: collection of differences between lists
    """
    for line in list1:
        if line not in list2:
            diff_list.append(FILE1_SIGN + line)
    for line in list2:
        if line not in list1:
            diff_list.append(FILE2_SIGN + line)


def compare_lists(list1, list2, first_col_comp, last_col_to_compare, diff_list, sec_format, comment_col):
    """
    Determine if section entries are meaningfully different. That is it ignores:
    * diffs in formatting
    * comments
    * X Y Z coords (for atoms)
    * order entry (for bonds, angles, dihedrals, and impropers
    For sections in which order does not matter (so first column, indicating order, is ignored), determine differences
    between entries (ignores diffs in formatting and comments)
    @param list1: list of lists containing entries for a section from one data file
    @param list2: same for a second data file
    @param first_col_comp: in the lists within the main list, the first col number to compare (the numbering
             col is irrelevant for bonds, angles, dihedrals, and impropers, but is for others)
    @param last_col_to_compare: the last col in the lists within the main list that should be compared (excludes
             notes, X, Y, Z coords for the Atoms section...)
    @param diff_list: collection of (meaningful) differences between lists
    @param sec_format: pretty formatting for non-comment columns (section-specific)
    @param comment_col: index of the comment column
    """
    # sets used to compare differences
    set1 = set()
    set2 = set()
    # dict used to connect whole line with set representation
    dict1 = {}
    dict2 = {}
    # temporary lists to allow sorting
    new_list1 = []
    new_list2 = []
    for line in list1:
        str_rep = str(line[first_col_comp:last_col_to_compare])
        set1.add(str_rep)
        dict1[str_rep] = line
    for line in list2:
        str_rep = str(line[first_col_comp:last_col_to_compare])
        set2.add(str_rep)
        dict2[str_rep] = line
    only1 = list(set1.difference(set2))
    only2 = list(set2.difference(set1))
    for entry in only1:
        new_list1.append([FILE1_SIGN] + dict1[entry])
    for entry in only2:
        new_list2.append([FILE2_SIGN] + dict2[entry])

    # Now, check that they are truly different, not just because of floating point representation
    # Only the sections that have first_col_comp == 0 have floats
    if first_col_comp == 0:
        float_dict1 = {}
        lines_to_remove1 = []
        float_dict2 = {}
        lines_to_remove2 = []
        for line1 in new_list1:
            # add one to col number because added the file sign to the beginning of the list
            float_dict1[line1[1]] = ([float(line1[x]) for x in range(first_col_comp+1, last_col_to_compare+1)], line1)
        for line2 in new_list2:
            # add one to col number because added the file sign to the beginning of the list
            float_dict2[line2[1]] = ([float(line2[x]) for x in range(first_col_comp+1, last_col_to_compare+1)], line2)
        for line_key in float_dict1:
            if line_key in float_dict2:
                within_tol = True
                for col1, col2 in zip(float_dict1[line_key][0], float_dict2[line_key][0]):
                    # if difference greater than the tolerance, the difference is not just precision
                    float_diff = abs(col1 - col2)
                    calc_tol = max(COMP_TOL * max(abs(col1), abs(col2)), COMP_TOL)
                    if float_diff > calc_tol:
                        within_tol = False
                        break
                if within_tol:
                    lines_to_remove1.append(float_dict1[line_key][1])
                    lines_to_remove2.append(float_dict2[line_key][1])
        for line in lines_to_remove1:
            new_list1.remove(line)
        for line in lines_to_remove2:
            new_list2.remove(line)

    new_list1 = sorted(new_list1, key=itemgetter(1))
    new_list2 = sorted(new_list2, key=itemgetter(1))

    for line in new_list1 + new_list2:
        diff_list.append(line[0] + sec_format.format(*line[1:comment_col+1]) + " ".join(line[comment_col+1:]))


def comp_files(cfg, atom_id_dict, type_dicts):
    """
    Compares each section of data files
    @param cfg: configuration information for current run
    @param atom_id_dict: dictionary for changing the atom id
    @param type_dicts: dictionary for changing atom and interaction types
    @return:
    """
    first_content, first_section_order = proc_data_file(cfg, cfg[DATA_FILE], atom_id_dict, type_dicts,)
    second_content, second_section_order = proc_data_file(cfg, cfg[DATA_COMP], atom_id_dict, type_dicts,)

    for section in second_section_order:
        if section not in first_section_order:
            warning("Skipping section '{}'; section found in the file: {}\n"
                    "   but not in file: {}".format(section, cfg[DATA_COMP], cfg[DATA_FILE]))

    diffs = ["Differences in head section:"]
    compare_heads(first_content[SEC_HEAD], second_content[SEC_HEAD], diffs)

    for section in first_section_order:
        if section not in second_section_order:
            warning("Skipping section '{}'; section found in the file: {}\n"
                    "   but not in file: {}".format(section, cfg[DATA_FILE], cfg[DATA_COMP]))
        elif section in [SEC_VELOS]:
            diffs.append("\nSkipping section '{}'".format(section))
        elif section in COMP_ORD_SEC_COL_DICT:
            diffs.append("\nDifferences in section '{}':".format(section))
            num_col_to_compare = COMP_ORD_SEC_COL_DICT[section]
            compare_lists(first_content[section], second_content[section], 0, num_col_to_compare, diffs,
                          SEC_FORMAT_DICT[section][0], SEC_FORMAT_DICT[section][1])
        elif section in NUM_SEC_DICT:
            diffs.append("\nDifferences in section '{}':".format(section))
            num_col_to_compare = NUM_SEC_DICT[section][1]
            compare_lists(first_content[section], second_content[section], 1, num_col_to_compare, diffs,
                          SEC_FORMAT_DICT[section][0], SEC_FORMAT_DICT[section][1])
        else:
            print("Encountered unexpected section '{}'".format(section))

    f_name = create_out_fname(cfg[DATA_COMP], prefix='diffs_', ext='.txt')
    list_to_file(diffs, f_name)
    print('Completed writing {}'.format(f_name))


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
        if cfg[DATA_COMP] is None:
            process_data_files(cfg, atom_id_dict, type_dicts)
        else:
            comp_files(cfg, atom_id_dict, type_dicts)
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
