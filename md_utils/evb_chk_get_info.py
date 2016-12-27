#!/usr/bin/env python
"""
Get selected info from the file
"""

from __future__ import print_function

import os
import re
import sys
import argparse
import numpy as np
from md_utils.md_common import (InvalidDataError, warning, create_out_fname, process_cfg,
                                print_qm_kind, IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, read_csv_dict,
                                file_rows_to_list, write_csv)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser


__author__ = 'hmayes'

# Constants #

# Config File Sections
MAIN_SEC = 'main'
REL_E_SEC = 'rel_e'

# Config keys
CHK_FILE_LIST = 'evb_chk_file_list'
LAST_EXCLUDE_ID = 'exclude_atom_ids_through'
OUT_BASE_DIR = 'output_base_directory'
EXPECTED_CHARGE = 'expected_charge'
REF_E_FILE = 'ref_e_file'

# Defaults
DEF_CFG_FILE = 'evb_chk_get_info.ini'
# Set notation
DEF_CFG_VALS = {LAST_EXCLUDE_ID: 0, OUT_BASE_DIR: None,
                EXPECTED_CHARGE: None,
                REF_E_FILE: None,
                }
REQ_KEYS = {CHK_FILE_LIST: str,
            }

# Sections
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'

# Content
NUM_ATOMS = 'num_atoms'
HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'

FILE_NAME = 'filename'
NUM_ATOMS_PAT = re.compile(r"^ATOMS (\d+).*")
ENE_ENERGY_PAT = re.compile(r"^ENV_ENERGY.*")
REL_E_PAT = 'rel_e_pat'
REL_E = 'rel_e'
REF_E = 'ref_e'
E_RESID = 'e_resid'
REL_E_REF = 'rel_e_ref'
REL_E_GROUP = 'rel_e_group'
ENV_ENE = 'env_e'
ENE_FIELD_NAMES = [FILE_NAME, REL_E_GROUP, REL_E, REF_E, E_RESID, ENV_ENE, ]


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
        raise IOError('Could not read file {}'.format(floc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)
    if main_proc[EXPECTED_CHARGE] is not None:
        main_proc[EXPECTED_CHARGE] = int(main_proc[EXPECTED_CHARGE])
    rel_e_proc = {}
    if REL_E_SEC in config.sections():
        for entry in config.items(REL_E_SEC):
            section_prefix = entry[0]
            # when the ini file is read, upper case becomes lower, so I'll ignore case in pattern matching
            base_e_match_pat = re.compile(r".*" + section_prefix + ".*", re.I)
            base_e_file_name = entry[1]
            rel_e_proc[section_prefix] = {REL_E_PAT: base_e_match_pat,
                                          FILE_NAME: base_e_file_name,
                                          REL_E_REF: np.nan, }
    main_proc[REL_E_SEC] = rel_e_proc

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
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def print_vmd_list(atom_ids, fname, mode='w'):
    # Change to base zero for VMD
    vmd_atom_ids = [a_id - 1 for a_id in atom_ids]
    with open(fname, mode) as m_file:
        m_file.write('{}'.format(' '.join(map(str, vmd_atom_ids))))
    print("Wrote file: {}".format(fname))


def get_evb_atoms(cfg, chk_file):

    with open(chk_file) as d:
        chk_data = {HEAD_CONTENT: [], ATOMS_CONTENT: [], TAIL_CONTENT: []}

        section = SEC_HEAD
        o_ids = []
        h_ids = []

        for line in d:
            line = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                chk_data[HEAD_CONTENT].append(line)

                atoms_match = NUM_ATOMS_PAT.match(line)
                if atoms_match:
                    # regex is 1-based
                    # print(atoms_match.group(1))
                    chk_data[NUM_ATOMS] = int(atoms_match.group(1))
                    section = SEC_ATOMS

            elif section == SEC_ATOMS:
                if len(line) == 0:
                    continue
                split_line = line.split()
                index = int(split_line[0])
                atom_num = int(split_line[1])
                x, y, z = map(float, split_line[2:5])
                atom_type = split_line[5]
                atom_struct = [index, atom_num, x, y, z, atom_type]
                chk_data[ATOMS_CONTENT].append(atom_struct)
                if atom_num > cfg[LAST_EXCLUDE_ID]:
                    if atom_type == 'O':
                        o_ids.append(atom_num)
                    elif atom_type == 'H':
                        h_ids.append(atom_num)
                    else:
                        raise InvalidDataError("Expected atom types are 'O' and 'H' (looking for water "
                                               "molecules only). Found type '{}' for line:\n {}\n"
                                               "Use the '{}' keyword to specify the last atom to exclude (i.e. "
                                               "the last protein atom)."
                                               "".format(atom_type, line, LAST_EXCLUDE_ID))

                if len(chk_data[ATOMS_CONTENT]) == chk_data[NUM_ATOMS]:
                    section = SEC_TAIL
            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                break

    # Data validation: checking total charge
    num_o = len(o_ids)
    num_h = len(h_ids)
    total_charge = num_h - 2 * num_o
    if cfg[EXPECTED_CHARGE] is None:
        print("Found {} oxygen atoms and {} hydrogen atoms for a total charge of {}."
              "".format(num_o, num_h, add_sign(total_charge)))
    else:
        if total_charge != cfg[EXPECTED_CHARGE]:
            raise InvalidDataError("Expected a total charge of {} but found {} for file: {}"
                                   "".format(add_sign(cfg[EXPECTED_CHARGE]), add_sign(total_charge), chk_file))

    # printing!
    f_name = create_out_fname(chk_file, prefix='water_', ext='.dat', base_dir=cfg[OUT_BASE_DIR],
                              remove_prefix='CHK_')
    print_qm_kind(h_ids, 'H', f_name)
    print_qm_kind(o_ids, 'O', f_name, mode='a')
    f_name = create_out_fname(chk_file, prefix='vmd_water_', ext='.dat', base_dir=cfg[OUT_BASE_DIR],
                              remove_prefix='CHK_')
    print_vmd_list(o_ids+h_ids, f_name)


def add_sign(val):
    if val > 0:
        return "+" + str(val)
    else:
        return val


def get_ene_data(cfg, chk_file_list):
    """
    Get environmental energy
    @param cfg: configuration for run
    @param chk_file_list: a list of files to process
    @return: a list of dicts
    """
    chk_dict_list = []
    for chk_file in chk_file_list:
        with open(chk_file) as d:
            base_file_name = os.path.basename(chk_file)
            chk_file_dict = {FILE_NAME: base_file_name}
            rel_e_group = None
            for group, rel_e_dict in cfg[REL_E_SEC].items():
                if rel_e_dict[REL_E_PAT].match(base_file_name):
                    rel_e_group = group
                    chk_file_dict[REL_E_GROUP] = rel_e_group
                    break
            for line in d:
                line = line.strip()
                if ENE_ENERGY_PAT.match(line):
                    ene_total = float(line.split()[1])
                    chk_file_dict[ENV_ENE] = ene_total
                    if rel_e_group is not None:
                        if base_file_name == cfg[REL_E_SEC][rel_e_group][FILE_NAME]:
                            cfg[REL_E_SEC][rel_e_group][REL_E_REF] = ene_total
                    chk_dict_list.append(chk_file_dict)
                    break
    return chk_dict_list


def find_rel_e(extracted_data, cfg, ref_e_dict):
    """
    calculate relative energy, if data found
    @param extracted_data: dictionary of data found from chk file
    @param cfg: configuration for run
    @param ref_e_dict: reference energies, if available
    @return:
    """

    tot_resid = 0
    num_resid = 0

    for data_dict in extracted_data:
        this_group = data_dict[REL_E_GROUP]
        if this_group:
            rel_ene_ref = cfg[REL_E_SEC][this_group][REL_E_REF]
        if this_group is None or np.isnan(rel_ene_ref):
            data_dict[REL_E] = np.nan
        else:
            rel_e = data_dict[ENV_ENE] - rel_ene_ref
            data_dict[REL_E] = rel_e
            file_name = data_dict[FILE_NAME]
            if file_name in ref_e_dict:
                ref_e = ref_e_dict[file_name]
                resid = np.round(np.sqrt((ref_e - rel_e) ** 2), 6)

                data_dict[REF_E] = ref_e
                data_dict[E_RESID] = resid
                tot_resid += resid
                num_resid += 1

    f_out = create_out_fname(cfg[CHK_FILE_LIST], suffix='_sum', ext='.csv',
                             base_dir=cfg[OUT_BASE_DIR])
    write_csv(extracted_data, f_out, ENE_FIELD_NAMES, extrasaction="ignore")
    if len(ref_e_dict) > 1:
        print("Calculated total energy residual from {} files: {}".format(num_resid, tot_resid))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    # Read template and data files
    cfg = args.config

    try:
        chk_file_list = file_rows_to_list(cfg[CHK_FILE_LIST])
        if len(cfg[REL_E_SEC]) > 0:
            extracted_data = get_ene_data(cfg, chk_file_list)
            ref_e_dict = read_csv_dict(cfg[REF_E_FILE], one_to_one=False, str_float=True)
            find_rel_e(extracted_data, cfg, ref_e_dict)
        else:
            for chK_file in chk_file_list:
                get_evb_atoms(cfg, chK_file)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    # print(psf_data_content[ATOMS_CONTENT])
    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
