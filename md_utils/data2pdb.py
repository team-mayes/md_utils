#!/usr/bin/env python
"""
Creates pdb data files from lammps data files, given a template pdb file.
"""

from __future__ import print_function
# noinspection PyCompatibility
import ConfigParser
import os
from collections import defaultdict
import copy
import json
import logging
import re
import sys
import argparse

from md_utils.md_common import InvalidDataError, warning, process_cfg, create_out_fname, list_to_file

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
PDB_TPL_FILE = 'pdb_tpl_file'
DATA_FILES_FILE = 'data_list_file'
DATA_FILES = 'data_files_list'
DATA_FILE = 'data_file'
ATOM_TYPE_DICT_FILE = 'atom_type_dict_file'
CENTER_ATOM = 'center_to_atom_num'
# PDB file info
PDB_LINE_TYPE_LAST_CHAR = 'pdb_line_type_last_char'
PDB_ATOM_NUM_LAST_CHAR = 'pdb_atom_num_last_char'
PDB_ATOM_TYPE_LAST_CHAR = 'pdb_atom_type_last_char'
PDB_RES_TYPE_LAST_CHAR = 'pdb_res_type_last_char'
PDB_MOL_NUM_LAST_CHAR = 'pdb_mol_num_last_char'
PDB_X_LAST_CHAR = 'pdb_x_last_char'
PDB_Y_LAST_CHAR = 'pdb_y_last_char'
PDB_Z_LAST_CHAR = 'pdb_z_last_char'
PDB_FORMAT = 'pdb_print_format'
LAST_PROT_ID = 'last_prot_atom'
OUT_BASE_DIR = 'output_directory'
MAKE_DICT_BOOL = 'make_dictionary_flag'
CHECK_ATOM_TYPE = 'use_atom_dict_flag'

ATOMS_PAT = re.compile(r"^Atoms.*")
NUM_ATOMS_PAT = re.compile(r"(\d+).*atoms$")

# data file info

# Defaults
DEF_CFG_FILE = 'data2pdb.ini'
# Set notation
DEF_CFG_VALS = {DATA_FILES_FILE: 'data_list.txt', ATOM_TYPE_DICT_FILE: 'atom_dict.json',
                PDB_FORMAT: '{:s}{:s}{:s}{:s}{:4d}    {:8.3f}{:8.3f}{:8.3f}{:s}',
                PDB_LINE_TYPE_LAST_CHAR: 6,
                PDB_ATOM_NUM_LAST_CHAR: 11,
                PDB_ATOM_TYPE_LAST_CHAR: 17,
                PDB_RES_TYPE_LAST_CHAR: 22,
                PDB_MOL_NUM_LAST_CHAR: 28,
                PDB_X_LAST_CHAR: 38,
                PDB_Y_LAST_CHAR: 46,
                PDB_Z_LAST_CHAR: 54,
                LAST_PROT_ID: 0,
                OUT_BASE_DIR: None,
                MAKE_DICT_BOOL: False,
                CHECK_ATOM_TYPE: False,
                DATA_FILE: None,
                }
REQ_KEYS = {PDB_TPL_FILE: str,
            }

# From data template file
NUM_ATOMS = 'num_atoms'
HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'

# For data template file processing
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'


def read_cfg(f_loc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param f_loc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser.ConfigParser()
    good_files = config.read(f_loc)

    if not good_files:
        raise IOError('Could not read file {}'.format(f_loc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)

    # To fix; have this as default!
    main_proc[DATA_FILES] = []
    if os.path.isfile(main_proc[DATA_FILES_FILE]):
        with open(main_proc[DATA_FILES_FILE]) as f:
            for data_file in f:
                main_proc[DATA_FILES].append(data_file.strip())
    if main_proc[DATA_FILE] is not None:
        main_proc[DATA_FILES].append(main_proc[DATA_FILE])
    if len(main_proc[DATA_FILES]) == 0:
        raise InvalidDataError("No files to process: no '{}' specified and "
                               "no list of files found for: {}".format(DATA_FILE, main_proc[DATA_FILES_FILE]))

    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates pdb files from lammps data, given a template pdb file.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
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
    except (InvalidDataError, ConfigParser.MissingSectionHeaderError) as e:
        warning(e)
        parser.print_help()
        return args, INVALID_DATA

    return args, GOOD_RET


def process_pdb_tpl(cfg):
    tpl_loc = cfg[PDB_TPL_FILE]
    tpl_data = {HEAD_CONTENT: [], ATOMS_CONTENT: [], TAIL_CONTENT: []}

    atom_id = 0

    with open(tpl_loc) as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            line_head = line[:cfg[PDB_LINE_TYPE_LAST_CHAR]]
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            # match 5 letters so don't need to set up regex for the ones that have numbers following the letters
            # noinspection SpellCheckingInspection
            if line_head[:-1] in ['HEADE', 'TITLE', 'REMAR', 'CRYST', 'MODEL', 'COMPN',
                                  'NUMMD', 'ORIGX', 'SCALE', 'SOURC', 'AUTHO', 'CAVEA',
                                  'EXPDT', 'MDLTY', 'KEYWD', 'OBSLT', 'SPLIT', 'SPRSD',
                                  'REVDA', 'JRNL ', 'DBREF', 'SEQRE', 'HET  ', 'HETNA',
                                  'HETSY', 'FORMU', 'HELIX', 'SHEET', 'SSBON', 'LINK ',
                                  'CISPE', 'SITE ', ]:
                tpl_data[HEAD_CONTENT].append(line)

            # atoms_content to contain everything but the xyz
            elif line_head == 'ATOM  ':

                # By renumbering, handles the case when a PDB template has ***** after atom_id 99999.
                # For renumbering, making sure prints in the correct format, including num of characters:
                atom_id += 1
                if atom_id > 99999:
                    atom_num = format(atom_id, 'x')
                else:
                    atom_num = '{:5d}'.format(atom_id)
                # Alternately, use this:
                # atom_num = line[cfg[PDB_LINE_TYPE_LAST_CHAR]:cfg[PDB_ATOM_NUM_LAST_CHAR]]

                atom_type = line[cfg[PDB_ATOM_NUM_LAST_CHAR]:cfg[PDB_ATOM_TYPE_LAST_CHAR]]
                res_type = line[cfg[PDB_ATOM_TYPE_LAST_CHAR]:cfg[PDB_RES_TYPE_LAST_CHAR]]
                # There is already a try when calling the subroutine, so maybe I don't need to?
                mol_num = int(line[cfg[PDB_RES_TYPE_LAST_CHAR]:cfg[PDB_MOL_NUM_LAST_CHAR]])
                pdb_x = float(line[cfg[PDB_MOL_NUM_LAST_CHAR]:cfg[PDB_X_LAST_CHAR]])
                pdb_y = float(line[cfg[PDB_X_LAST_CHAR]:cfg[PDB_Y_LAST_CHAR]])
                pdb_z = float(line[cfg[PDB_Y_LAST_CHAR]:cfg[PDB_Z_LAST_CHAR]])
                last_cols = line[cfg[PDB_Z_LAST_CHAR]:]

                line_struct = [line_head, atom_num, atom_type, res_type, mol_num, pdb_x, pdb_y, pdb_z, last_cols]
                tpl_data[ATOMS_CONTENT].append(line_struct)

            # tail_content to contain everything after the 'Atoms' section
            else:
                tpl_data[TAIL_CONTENT].append(line)

    if logger.isEnabledFor(logging.DEBUG):
        f_name = create_out_fname('reproduced_tpl', ext='.pdb', base_dir=cfg[OUT_BASE_DIR])
        list_to_file(tpl_data[HEAD_CONTENT] + tpl_data[ATOMS_CONTENT] + tpl_data[TAIL_CONTENT],
                     f_name, list_format=cfg[PDB_FORMAT])
    return tpl_data


def make_dict(cfg, data_tpl_content):
    atoms_pat = re.compile(r"^Atoms.*")
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    matched_atom_types = {}
    atom_type_dict = defaultdict(list)
    non_unique_charmm = []
    pdb_atom_num = len(data_tpl_content[ATOMS_CONTENT])
    for data_file in cfg[DATA_FILES]:
        with open(data_file) as d:
            section = SEC_HEAD
            atom_id = 0
            num_atoms = None
            for line in d:
                line = line.strip()
                # not currently keeping anything from the header; just check num atoms
                if section == SEC_HEAD:
                    if atoms_pat.match(line):
                        section = SEC_ATOMS
                    elif num_atoms is None:
                        atoms_match = num_atoms_pat.match(line)
                        if atoms_match:
                            # regex is 1-based
                            num_atoms = int(atoms_match.group(1))
                            if num_atoms != pdb_atom_num:
                                raise InvalidDataError("Mismatched numbers of atoms: \n"
                                                       "  Found {} atoms in file: {}\n"
                                                       "    and {} atoms in file: {}\n"
                                                       "".format(pdb_atom_num, cfg[PDB_TPL_FILE],
                                                                 num_atoms, data_file))
                elif section == SEC_ATOMS:
                    if len(line) == 0:
                        continue
                    split_line = line.split()

                    # keep lammps types as strings, because json saves as strings to be portable
                    lammps_atom_type = split_line[2]
                    # combine atom type with molecules/resid type
                    charmm_atom_type = (data_tpl_content[ATOMS_CONTENT][atom_id][2] +
                                        data_tpl_content[ATOMS_CONTENT][atom_id][3])

                    # Making the dictionary; use charmm as unique key. Do this first to verify library.
                    if charmm_atom_type in matched_atom_types:
                        # Check that we don't have conflicting matching
                        if lammps_atom_type != matched_atom_types[charmm_atom_type]:
                            if charmm_atom_type not in non_unique_charmm:
                                print('Verify that this charmm type can have multiple lammps types: ',
                                      charmm_atom_type)
                                print('First collision for this charmm type occurred on atom:', atom_id + 1)
                                non_unique_charmm.append(charmm_atom_type)
                    else:
                        matched_atom_types[charmm_atom_type] = lammps_atom_type

                    # Don't add if already there
                    if charmm_atom_type not in atom_type_dict[lammps_atom_type]:
                        atom_type_dict[lammps_atom_type].append(charmm_atom_type)

                    atom_id += 1
                    # Check after increment because the counter started at 0
                    if atom_id == num_atoms:
                        # Since the tail will come only from the template, nothing more is needed.
                        break
        print('Finished looking for dictionary values in file ', data_file)

    with open(cfg[ATOM_TYPE_DICT_FILE], 'w') as d_file:
        json.dump(atom_type_dict, d_file)

    print('Completed making dictionary and saved it to {}'.format(cfg[ATOM_TYPE_DICT_FILE]))


def process_data_files(cfg, data_tpl_content):
    # Don't want to change the original template data when preparing to print the new file:

    chk_atom_type = cfg[CHECK_ATOM_TYPE]
    data_dict = {}

    if chk_atom_type:
        try:
            with open(cfg[ATOM_TYPE_DICT_FILE], 'r') as d_file:
                data_dict = json.load(d_file)
        except IOError as e:
            warning("Problems reading dictionary file: {}\n"
                    "The program will continue without checking atom types.".format(cfg[ATOM_TYPE_DICT_FILE]), e)
            chk_atom_type = False

    for data_file in cfg[DATA_FILES]:
        process_data_file(cfg, chk_atom_type, data_dict, data_file, data_tpl_content)


def process_data_file(cfg, chk_atom_type, data_dict, data_file, data_tpl_content):
    with open(data_file) as d:
        pdb_data_section = copy.deepcopy(data_tpl_content[ATOMS_CONTENT])
        pdb_atom_num = len(pdb_data_section)
        section = SEC_HEAD
        atom_id = 0
        num_atoms = None
        atom_types = []

        for line in d:
            line = line.strip()
            # not currently keeping anything from the header; just check num atoms
            if section == SEC_HEAD:
                if ATOMS_PAT.match(line):
                    section = SEC_ATOMS
                elif num_atoms is None:
                    atoms_match = NUM_ATOMS_PAT.match(line)
                    if atoms_match:
                        # regex is 1-based
                        num_atoms = int(atoms_match.group(1))
                        if num_atoms != pdb_atom_num:
                            raise InvalidDataError("Mismatched numbers of atoms: \n"
                                                   "  Found {} atoms in file: {}\n"
                                                   "    and {} atoms in file: {}\n"
                                                   "".format(pdb_atom_num, cfg[PDB_TPL_FILE],
                                                             num_atoms, data_file))

            # atoms_content to contain only xyz; also perform some checking
            elif section == SEC_ATOMS:
                if len(line) == 0:
                    continue
                split_line = line.split()

                # Not currently checking molecule number
                # If decide to do so, should make a count from 1 as the PDB is read; the PDB does not
                # have to start from 1, but the data file counts molecules from 1. For now, decided
                # checking atom type is a sufficient check
                # mol_num = int(split_line[1])

                # Keep as string; json save as string and this helps compare
                atom_types.append(split_line[2])
                pdb_data_section[atom_id][5:8] = map(float, split_line[4:7])
                atom_id += 1
                # Check after increment because the counter started at 0
                if atom_id == num_atoms:
                    # Since the tail will come only from the template, nothing more is needed.
                    break

    # Now that finished reading the file...
    if atom_id != num_atoms:
        raise InvalidDataError('In data file: {}\n'
                               '  header section lists {} atoms, but found {} atoms'.format(data_file,
                                                                                            num_atoms, atom_id))
    if chk_atom_type:
        for data_type, atom in zip(atom_types, pdb_data_section):
            try:
                pdb_type = atom[2] + atom[3]
                if pdb_type not in data_dict[data_type]:
                    warning('Did not find type {} in dictionary of values for atom_type {}: ({})'
                            ''.format(pdb_type, data_type, data_dict[data_type]))
                    # print("atom", atom_type, data_dict[atom_type])
            except KeyError:
                warning('Did not find data file atom type {} in the atom type dictionary {}'
                        ''.format(data_type, cfg[ATOM_TYPE_DICT_FILE]))
    f_name = create_out_fname(data_file, ext='.pdb', base_dir=cfg[OUT_BASE_DIR])
    list_to_file(data_tpl_content[HEAD_CONTENT] + pdb_data_section + data_tpl_content[TAIL_CONTENT],
                 f_name,
                 list_format=cfg[PDB_FORMAT])
    print('Completed writing {}'.format(f_name))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    cfg = args.config

    # Read template and data files
    try:
        pdb_tpl_content = process_pdb_tpl(cfg)
        # TODO: Test and use dictionary
        if cfg[MAKE_DICT_BOOL]:
            make_dict(cfg, pdb_tpl_content)
        process_data_files(cfg, pdb_tpl_content)
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
