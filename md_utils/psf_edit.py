#!/usr/bin/env python
# coding=utf-8
"""
Edit a psf file
"""

from __future__ import print_function
import os
import re
import sys
import argparse
from md_utils.md_common import InvalidDataError, read_csv_dict, warning, create_out_fname, process_cfg, list_to_file, \
    create_element_dict, print_qm_kind, print_qm_links
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
PSF_FILE = 'psf_file'
PSF_NEW_FILE = 'pdb_new_file'
OUT_BASE_DIR = 'output_directory'

ATOM_REORDER_FILE = 'atom_reorder_old_new_file'
MOL_RENUM_FILE = 'mol_renum_old_new_file'
RENUM_MOL = 'mol_renum_flag'
PSF_FORMAT = 'psf_print_format'
ELEMENT_DICT_FILE = 'atom_type_element_dict_file'
RESID_QMMM = 'resids_qmmm_ca_cb_link'

# Defaults
DEF_CFG_FILE = 'psf_edit.ini'
DEF_ELEM_DICT_FILE = os.path.join(os.path.dirname(__file__), 'cfg', 'charmm36_atoms_elements.txt')
# Set notation
DEF_CFG_VALS = {ATOM_REORDER_FILE: None,
                MOL_RENUM_FILE: None,
                RENUM_MOL: False,
                OUT_BASE_DIR: None,
                PSF_NEW_FILE: None,
                PSF_FORMAT: '{:8d} {:5s}{:<5d}{:5s}{:5s}{:5s}{:10.6f}{:14.4f}{:>12s}',
                RESID_QMMM: [],
                ELEMENT_DICT_FILE: None,
                }
REQ_KEYS = {PSF_FILE: str,
            }

# Sections
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'
HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'

# Atom types; used for making QMMM input
C_ALPHA = 'CA'
C_BETA = 'CB'
SKIP_ATOM_TYPES = ['C', 'O', 'NT', 'HNT', 'CAT', 'HT1', 'HT2', 'HT3', 'HA', 'CAY',
                   'HY1', 'HY2', 'HY3', 'CY', 'OY', 'N', 'HN', ]


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
        raise IOError('Could not read file {}'.format(f_loc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)
    if (len(main_proc[RESID_QMMM]) > 0) and main_proc[ELEMENT_DICT_FILE] is None:
        main_proc[ELEMENT_DICT_FILE] = DEF_ELEM_DICT_FILE
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates a new version of a psf file. '
                                                 'Options include renumbering molecules.')
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

    return args, GOOD_RET


def process_psf(cfg, atom_num_dict, mol_num_dict, element_dict):

    with open(cfg[PSF_FILE]) as f:
        psf_data = {HEAD_CONTENT: [], ATOMS_CONTENT: [], TAIL_CONTENT: []}
        num_atoms_pat = re.compile(r"(\d+).*NATOM$")

        num_atoms = 1
        section = SEC_HEAD

        # for printing qmmm info
        qmmm_elem_id_dict = {}
        ca_res_atom_id_dict = {}
        cb_res_atom_id_dict = {}
        qmmm_charge = 0

        for line in f.readlines():
            s_line = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                psf_data[HEAD_CONTENT].append(line.rstrip())

                atoms_match = num_atoms_pat.match(s_line)
                if atoms_match:
                    # regex is 1-based
                    num_atoms = int(atoms_match.group(1))
                    section = SEC_ATOMS

            elif section == SEC_ATOMS:
                if len(s_line) == 0:
                    continue
                split_line = s_line.split()
                atom_num = int(split_line[0])
                segid = split_line[1]
                resid = int(split_line[2])
                resname = split_line[3]
                atom_type = split_line[4]
                charmm_type = split_line[5]
                charge = float(split_line[6])
                atom_wt = float(split_line[7])
                zero = split_line[8]

                # For reordering atoms
                if atom_num in atom_num_dict:
                    atom_num = atom_num_dict[atom_num]

                # For user-specified changing of molecule number
                if resid in mol_num_dict:
                    resid = mol_num_dict[resid]

                atom_struct = [atom_num, segid, resid, resname, atom_type, charmm_type, charge, atom_wt, zero]
                psf_data[ATOMS_CONTENT].append(atom_struct)

                if resid in cfg[RESID_QMMM] and atom_type not in SKIP_ATOM_TYPES:
                    if atom_type == C_ALPHA:
                        ca_res_atom_id_dict[resid] = atom_num
                    else:
                        if atom_type == C_BETA:
                            cb_res_atom_id_dict[resid] = atom_num
                        if atom_type in element_dict:
                            element = element_dict[atom_type]
                        else:
                            raise InvalidDataError("Did not find atom type '{}' in the element dictionary. Please "
                                                   "provide a new atom type, element dictionary (using keyword {} "
                                                   "in the configuration file) that includes all atom types in the "
                                                   "residues identified with the '{}' key."
                                                   "".format(atom_type, ELEMENT_DICT_FILE, RESID_QMMM))
                        if element in qmmm_elem_id_dict:
                            qmmm_elem_id_dict[element].append(atom_num)
                        else:
                            qmmm_elem_id_dict[element] = [atom_num]
                        qmmm_charge += charge

                if len(psf_data[ATOMS_CONTENT]) == num_atoms:
                    section = SEC_TAIL
            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                psf_data[TAIL_CONTENT].append(line.rstrip())

    if len(atom_num_dict) > 0:
        warning("This program does not yet edit any sections other than the atoms section."
                "If you are renumbering atoms, the bonds, angles, dihedrals, impropers, and"
                "cross-terms sections will not match.")
        psf_data[ATOMS_CONTENT] = sorted(psf_data[ATOMS_CONTENT], key=lambda entry: entry[0])

    if cfg[PSF_NEW_FILE] is None:
        f_name = create_out_fname(cfg[PSF_FILE], suffix="_new", base_dir=cfg[OUT_BASE_DIR])
    else:
        f_name = cfg[PSF_NEW_FILE]
    list_to_file(psf_data[HEAD_CONTENT] + psf_data[ATOMS_CONTENT] + psf_data[TAIL_CONTENT],
                 f_name, list_format=cfg[PSF_FORMAT])

    if len(cfg[RESID_QMMM]) > 0:
        f_name = create_out_fname('amino_id.dat', base_dir=cfg[OUT_BASE_DIR])
        print_mode = "w"
        for elem in qmmm_elem_id_dict:
            print_qm_kind(qmmm_elem_id_dict[elem], elem, f_name, mode=print_mode)
            print_mode = 'a'
        print_qm_links(ca_res_atom_id_dict, cb_res_atom_id_dict, f_name, mode=print_mode)
        print("Total charge from QMMM atoms: {}".format(qmmm_charge))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    cfg = args.config

    # Read and process pdb files
    try:
        atom_num_dict = read_csv_dict(cfg[ATOM_REORDER_FILE])
        mol_num_dict = read_csv_dict(cfg[MOL_RENUM_FILE], one_to_one=False)
        element_dict = create_element_dict(cfg[ELEMENT_DICT_FILE], pdb_dict=False)
        process_psf(cfg, atom_num_dict, mol_num_dict, element_dict)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems with input information:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
