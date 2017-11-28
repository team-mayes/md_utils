#!/usr/bin/env python
"""
Get information from cp2k output files, such as coordinates and final QMMM energy.
Given a template data or pdb file, it will make new files with the xyz coordinates from the cp2k output file
"""

from __future__ import print_function
import argparse
import os
import re
import sys
import numpy as np
from datetime import datetime

import md_utils
from md_utils.data2data import process_data_tpl

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser
from md_utils.md_common import (InvalidDataError, create_out_fname, warning, process_cfg,
                                list_to_file, file_rows_to_list, create_element_dict,
                                HEAD_CONTENT, ATOMS_CONTENT, TAIL_CONTENT, process_pdb_tpl, PDB_FORMAT)

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
DATA_TPL_FILE = 'data_tpl_file'
PDB_TPL_FILE = 'pdb_tpl_file'
CP2K_LIST_FILE = 'cp2k_list_file'
CP2K_FILE = 'cp2k_file'
XYZ_FILE_SUF = 'xyz_file_suffix'
PRINT_XYZ_FLAG = 'print_xyz_files'

# data file info

COORD_PAT = re.compile(r".*MODULE FIST: {2}ATOMIC COORDINATES IN.*")
ENERGY_PAT = re.compile(r".*ENERGY\| Total FORCE_EVAL \( QMMM \).*")
OUTER_CONV_PAT = re.compile(r".*outer SCF loop converged.*")
GEOM_OPT_RUN_PAT = re.compile(r".*Run type {56}GEO_OPT.*")
GEOM_OPT_COMPLETE_PAT = re.compile(r".*GEOMETRY OPTIMIZATION COMPLETED.*")
REF_PAT = re.compile(r".*R E F E R E N C E S.*")
NUM_ATOMS_PAT = re.compile(r"(\d+).*atoms$")
BOX_PAT = re.compile(r".*xhi")

# Defaults
DEF_CFG_FILE = 'cp2k_proc.ini'
ELEMENT_DICT_FILE = os.path.join(os.path.dirname(__file__), 'cfg', 'charmm36_atoms_elements.txt')
# Set notation
DEF_CFG_VALS = {CP2K_LIST_FILE: 'cp2k_files.txt', CP2K_FILE: None,
                DATA_TPL_FILE: None, PDB_TPL_FILE: None,
                PRINT_XYZ_FLAG: False, XYZ_FILE_SUF: '.xyz',
                }
REQ_KEYS = {}

# From template files
NUM_ATOMS = 'num_atoms'

# For cp2k file processing
CP2K_FILES = 'cp2k_file_list'
FILE_NAME = 'file_name'
QMMM_ENERGY = 'qmmm_energy'
OPT_GEOM = 'opt_geom'
COMPLETED_JOB = 'completed_job'


def read_cfg(floc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param floc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser()
    good_files = config.read(floc)
    if not good_files:
        raise IOError("Could not read file '{}'".format(floc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS, int_list=False)

    main_proc[CP2K_FILES] = []

    if os.path.isfile(main_proc[CP2K_LIST_FILE]):
        main_proc[CP2K_FILES] += file_rows_to_list(main_proc[CP2K_LIST_FILE])
    if main_proc[CP2K_FILE] is not None:
        main_proc[CP2K_FILES].append(main_proc[CP2K_FILE])

    if len(main_proc[CP2K_FILES]) == 0:
        raise InvalidDataError("Found no file names to process. Use the configuration ('ini') file to specify the name "
                               "of a single file with the keyword '{}' or a file with listing files to process "
                               "(one per line) with the keyword '{}'.".format(CP2K_FILE, CP2K_LIST_FILE))

    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Gathers data from cp2k output files, such as final system energy and '
                                                 'xyz coordinates. Options in the configuration file can lead to '
                                                 'creating data, pdb, or xyz files with the coordinates from the '
                                                 'cp2k output file.')
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
    except (InvalidDataError, KeyError, SystemExit) as e:
        if hasattr(e, 'code') and e.code == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def process_coords(cp2k_file, data_tpl_content, pdb_tpl_content, print_xyz_flag, element_dict):
    """
    Creates the new atoms section based on coordinates from the cp2k file
    @param cp2k_file: file being read
    @param data_tpl_content: data from the template file
    @param pdb_tpl_content: data from template file
    @param print_xyz_flag: boolean to make xyz files
    @param element_dict: a dictionary of MM types to atomic elements
    @return: new atoms section, with replaced coordinates
    """
    num_atoms = None
    if data_tpl_content is None:
        make_data_file = False
        new_atoms = []
    else:
        make_data_file = True
        new_atoms = list(data_tpl_content[ATOMS_CONTENT])
        num_atoms = data_tpl_content[NUM_ATOMS]

    if pdb_tpl_content is None:
        make_pdb_file = False
        new_pdb_atoms = []
    else:
        make_pdb_file = True
        new_pdb_atoms = list(pdb_tpl_content[ATOMS_CONTENT])
        if num_atoms is None:
            num_atoms = pdb_tpl_content[NUM_ATOMS]
        elif num_atoms != pdb_tpl_content[NUM_ATOMS]:
            raise InvalidDataError("Number of atoms from data temple ({}) does not equal the number in the pdb "
                                   "template ({})".format(data_tpl_content[NUM_ATOMS], pdb_tpl_content[NUM_ATOMS]))

    atoms_xyz = []
    atom_count = 0
    atom_num = 0
    for line in cp2k_file:
        split_line = line.split()
        if len(split_line) == 0:
            if num_atoms is None:
                # if can't stop because we are looking for a certain number of atoms, need this criterion
                return new_atoms, new_pdb_atoms, atoms_xyz
            else:
                # otherwise, should not be able to meet this criterion
                raise InvalidDataError("Encountered an empty line after reading {} atoms. Expected to read "
                                       "coordinates for {} atoms before encountering a blank line."
                                       "".format(atom_num, num_atoms))

        atom_num = int(split_line[0])
        xyz_coords = list(map(float, split_line[3:6]))
        if make_data_file:
            new_atoms[atom_count][4:7] = xyz_coords
        if make_pdb_file:
            new_pdb_atoms[atom_count][5:8] = xyz_coords
        if print_xyz_flag:
            # needs an atom type. If reading a PDB, use that; else the data file; lastly the CP2K file itself
            if make_pdb_file:
                charmm_type = new_pdb_atoms[atom_count][2].strip()
            elif make_data_file:
                charmm_type = new_atoms[atom_count][8].strip(',')
            else:
                charmm_type = split_line[2]
            try:
                element_type = element_dict[charmm_type]
            except KeyError:
                warning("Did not find the element type for '{}'; printing this type in the xyz file."
                        "".format(charmm_type))
                # Now add to element dict so don't get the same error printed multiple times
                element_dict[charmm_type] = charmm_type
                element_type = charmm_type
            atoms_xyz.append([element_type] + xyz_coords)
        atom_count += 1

        if num_atoms is not None:
            if atom_num == num_atoms:
                # If that is the end of the atoms, the next line should be blank
                line = next(cp2k_file).strip()
                if len(line) == 0:
                    return new_atoms, new_pdb_atoms, atoms_xyz
                else:
                    raise InvalidDataError("After reading the number of atoms found in the template data file "
                                           "({}), did not encounter a blank line, but: {}"
                                           "".format(data_tpl_content[NUM_ATOMS], line))

    # if went through even line and didn't get all the atoms, catch the error
    raise InvalidDataError("Did not read coordinates from {} atoms in file: {}".format(data_tpl_content[NUM_ATOMS],
                                                                                       cp2k_file.name))


def process_cp2k_file(cfg, cp2k_file, data_tpl_content, pdb_tpl_content, element_dict):
    """
    Gather info from CP2K output file and update xyz data if needed
    @param cfg: confirmation for the run
    @param cp2k_file: the file to open
    @param data_tpl_content: list of lists
    @param pdb_tpl_content: list of lists
    @param element_dict: element dictionary for making xyz files
    @return: xyz coordinates info in data, pdb, and xyz formats (as needed)
    """
    data_atoms_section = []
    pdb_atoms_section = []

    if data_tpl_content is None:
        make_data_file = False
    else:
        make_data_file = True

    if pdb_tpl_content is None:
        make_pdb_file = False
    else:
        make_pdb_file = True

    result_dict = {FILE_NAME: cp2k_file, QMMM_ENERGY: np.inf, OPT_GEOM: 'NA', COMPLETED_JOB: False}
    atoms_xyz = None
    with open(cp2k_file) as f:
        pkg_version = md_utils.__version__
        # print(temp1)
        # pkg_version = pkg_resources.parse_version(md_utils.__version__)
        if make_pdb_file:
            pdb_tpl_content[HEAD_CONTENT][0] = "REMARK 450 Created on {} by {} version {}" \
                                               "".format(datetime.now(), __name__, pkg_version)
            pdb_tpl_content[HEAD_CONTENT][1] = "REMARK 450 from template {}".format(cfg[PDB_TPL_FILE])
            pdb_tpl_content[HEAD_CONTENT][2] = "REMARK 450 and coordinates from {}".format(cp2k_file)

        if make_data_file:
            data_tpl_content[HEAD_CONTENT][0] = "Created on {} by {} version {} from template file {} and " \
                                                "cp2k output file {}".format(datetime.now(), __name__,
                                                                             pkg_version,
                                                                             cfg[DATA_TPL_FILE], cp2k_file)
        for line in f:
            line = line.strip()
            if COORD_PAT.match(line):
                # Now advance to first line of coordinates
                for _ in range(3):
                    next(f)
                data_atoms_section, pdb_atoms_section, atoms_xyz = process_coords(f, data_tpl_content, pdb_tpl_content,
                                                                                  cfg[PRINT_XYZ_FLAG], element_dict)
            elif ENERGY_PAT.match(line):
                # skip steps that take further from the min energy
                qmmm_energy = float(line.split()[-1])
                if qmmm_energy < result_dict[QMMM_ENERGY]:
                    result_dict[QMMM_ENERGY] = qmmm_energy
            elif GEOM_OPT_RUN_PAT.match(line):
                # set to false because not optimized, overwriting "NA"
                result_dict[OPT_GEOM] = False
            elif GEOM_OPT_COMPLETE_PAT.match(line):
                result_dict[OPT_GEOM] = True
            elif REF_PAT.match(line):
                result_dict[COMPLETED_JOB] = True
                break

    # If we successfully returned the data_atoms_section, make new file
    if (make_data_file and len(data_atoms_section) == 0) or (make_pdb_file and len(pdb_atoms_section) == 0
                                                             ) or (cfg[PRINT_XYZ_FLAG] and len(atoms_xyz) == 0):
        raise InvalidDataError("Did not file atoms coordinates in file: {}".format(cp2k_file))
    print('"{file_name}",{qmmm_energy:f},"{opt_geom}","{completed_job}"'.format(**result_dict))
    if make_data_file:
        f_name = create_out_fname(cp2k_file, ext='.data')
        list_to_file(data_tpl_content[HEAD_CONTENT] + data_atoms_section + data_tpl_content[TAIL_CONTENT],
                     f_name, print_message=False)
    if make_pdb_file:
        f_name = create_out_fname(cp2k_file, ext='.pdb')
        list_to_file(pdb_tpl_content[HEAD_CONTENT] + pdb_atoms_section + pdb_tpl_content[TAIL_CONTENT],
                     f_name, list_format=PDB_FORMAT, print_message=False)
    if cfg[PRINT_XYZ_FLAG]:
        f_name = create_out_fname(cp2k_file, ext=cfg[XYZ_FILE_SUF])
        list_to_file(atoms_xyz, f_name, print_message=False)


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    # Read template and data files
    cfg = args.config

    try:
        if cfg[PDB_TPL_FILE] is None:
            pdb_tpl_content = None
        else:
            pdb_tpl_content = process_pdb_tpl(cfg[PDB_TPL_FILE])
            # add new row at the beginning for remark
            pdb_tpl_content[HEAD_CONTENT] = ["REMARK 450 "]*3 + pdb_tpl_content[HEAD_CONTENT]
        if cfg[DATA_TPL_FILE] is None:
            data_tpl_content = None
        else:
            data_tpl_content = process_data_tpl(cfg)

        element_dict = create_element_dict(ELEMENT_DICT_FILE, pdb_dict=False)

        print('"file_name","qmmm_energy","opt_complete","job_complete"')
        for cp2k_file in cfg[CP2K_FILES]:
            process_cp2k_file(cfg, cp2k_file, data_tpl_content, pdb_tpl_content, element_dict)

    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR

    except (InvalidDataError, KeyError, ValueError) as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
