#!/usr/bin/env python
# coding=utf-8
"""
Edit a psf file
"""

from __future__ import print_function
import ConfigParser
import logging
import re
import sys
import argparse

from md_utils.md_common import InvalidDataError, read_csv_dict, warning, create_out_fname, process_cfg, list_to_file

__author__ = 'hmayes'

# Logging
logger = logging.getLogger('psf_edit')
logging.basicConfig(filename='psf_edit.log', filemode='w', level=logging.DEBUG)
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
PSF_FILE = 'psf_file'
PSF_NEW_FILE = 'pdb_new_file'
OUT_BASE_DIR = 'output_directory'

ATOM_REORDER_FILE = 'atom_reorder_old_new_file'
MOL_RENUM_FILE = 'mol_renum_old_new_file'
RENUM_MOL = 'mol_renum_flag'
PSF_FORMAT = 'psf_print_format'

# Defaults
DEF_CFG_FILE = 'psf_edit.ini'
# Set notation
DEF_CFG_VALS = {ATOM_REORDER_FILE: None,
                MOL_RENUM_FILE: None,
                RENUM_MOL: False,
                OUT_BASE_DIR: None,
                PSF_NEW_FILE: 'new.psf',
                PSF_FORMAT: '{:8d} {:5s}{:<5d}{:5s}{:5s}{:5s}{:10.6f}{:14.4f}{:>12s}',
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


def process_psf(cfg, atom_num_dict, mol_num_dict):

    with open(cfg[PSF_FILE]) as f:
        psf_data = {HEAD_CONTENT: [], ATOMS_CONTENT: [], TAIL_CONTENT: []}
        num_atoms_pat = re.compile(r"(\d+).*NATOM$")

        num_atoms = 1
        section = SEC_HEAD

        for line in f.readlines():
            sline = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                psf_data[HEAD_CONTENT].append(line.rstrip())

                atoms_match = num_atoms_pat.match(sline)
                if atoms_match:
                    # regex is 1-based
                    num_atoms = int(atoms_match.group(1))
                    section = SEC_ATOMS

            elif section == SEC_ATOMS:
                if len(sline) == 0:
                    continue
                split_line = sline.split()
                atom_num = int(split_line[0])
                segid = split_line[1]
                resid = int(split_line[2])
                resname = split_line[3]
                atom_type = split_line[4]
                charmm_type =  split_line[5]
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

    f_name = create_out_fname(cfg[PSF_NEW_FILE], base_dir=cfg[OUT_BASE_DIR])
    list_to_file(psf_data[HEAD_CONTENT] + psf_data[ATOMS_CONTENT] + psf_data[TAIL_CONTENT],
                 f_name,
                 list_format=cfg[PSF_FORMAT])

    return


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
        process_psf(cfg, atom_num_dict, mol_num_dict)
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
