#!/usr/bin/env python
"""
Creates lammps data files from lammps dump files, given a template lammps data file.
"""

from __future__ import print_function
import ConfigParser
from collections import defaultdict
import logging
import re
import sys
import argparse

import numpy as np

from md_utils.md_common import list_to_file, InvalidDataError, create_out_fname, pbc_dist, \
    warning, process_cfg, find_dump_section_state


__author__ = 'hmayes'

# Logging
logger = logging.getLogger('evbd2d')
logging.basicConfig(filename='evbd2d.log', filemode='w', level=logging.DEBUG)
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
DATA_TPL_FILE = 'data_tpl_file'
DUMPS_FILE = 'dump_list_file'
WAT_O_TYPE = 'water_o_type'
WAT_H_TYPE = 'water_h_type'
H3O_O_TYPE = 'h3o_o_type'
H3O_H_TYPE = 'h3o_h_type'
PROT_RES_MOL_ID = 'prot_res_mol_id'
PROT_H_TYPE = 'prot_h_type'
PROT_H_IGNORE = 'prot_ignore_h_atom_nums'
PROT_TYPE_IGNORE_ATOMS = 'prot_res_type_ignore_atoms'
OUT_BASE_DIR = 'output_directory'
REPROD_TPL = 'reproduce_tpl_flag'

PRE_RES = 'pre_prot_res'
PROT_RES = 'prot_res'
POST_RES = 'post_prot_res'
EXCESS_H = 'excess_proton'
HYD_MOL = 'h3o_mol'
WAT_MOL = 'wat_mol'
POST_WAT = 'post_wat'

# Config keys to allow calculating charge at intermediate points:
LAST_P1 = 'last_p1'
LAST_P2 = 'last_p2'
LONE_ION = 'lone_ion'
LAST_LIPID = 'last_lipid'
LAST_HYD = 'last_hyd'
LAST_WATER = 'last_water'
LAST_ION1 = 'last_ion1'

# Defaults
DEF_CFG_FILE = 'evbd2d.ini'
# Set notation
DEF_CFG_VALS = {DUMPS_FILE: 'dump_list.txt',
                PROT_H_IGNORE: [],
                OUT_BASE_DIR: None,
                LAST_P1: -1,
                LAST_P2: -1,
                LONE_ION: -1,
                LAST_LIPID: -1,
                LAST_HYD: -1,
                LAST_WATER: -1,
                LAST_ION1: -1,
                REPROD_TPL: False,
                PROT_TYPE_IGNORE_ATOMS: [],
                }
REQ_KEYS = {DATA_TPL_FILE: str,
            WAT_O_TYPE: int,
            WAT_H_TYPE: int,
            H3O_O_TYPE: int,
            H3O_H_TYPE: int,
            PROT_RES_MOL_ID: int,
            PROT_H_TYPE: int, }

# From data template file
NUM_ATOMS = 'num_atoms'
TAIL_CONTENT = 'tail_content'
ATOMS_CONTENT = 'atoms_content'
HEAD_CONTENT = 'head_content'
H3O_MOL = 'hydronium_molecule'
H3O_O_CHARGE = 'hydronium_o_charge'
H3O_H_CHARGE = 'hydronium_h_charge'
FIRST_H3O_H_INDEX = 'first h3o hydrogen index'
PROT_RES_MOL = 'protonatable_residue_molecule'
WATER_MOLS = 'template_water_molecules'


# For data template file processing
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'


# For dump file processing
SEC_TIMESTEP = 'timestep'
SEC_NUM_ATOMS = 'dump_num_atoms'
SEC_BOX_SIZE = 'dump_box_size'

# For deciding if a float is close enough to a value
TOL = 0.000001
# Bundle of headers for calculating charge
CALC_CHARGE_NAMES = [LAST_P1, LAST_P2, LONE_ION, LAST_LIPID, LAST_HYD, LAST_WATER, LAST_ION1]


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
    parser = argparse.ArgumentParser(description='Creates lammps data files from lammps dump files, given a template '
                                                 'lammps data file. The required input file provides the location of '
                                                 'the data template file, a file with a list of dump files to convert, '
                                                 'and information about the configuration of the data file, needed to '
                                                 'process the dump file to produce data files matching the template '
                                                 '(consistent ID for the hydronium ion, protonatable residue always'
                                                 'deprotonated, etc.). Currently, this script expects only one '
                                                 'protonatable residue.')
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
    except InvalidDataError as e:
        warning(e)
        return args, INVALID_DATA

    return args, GOOD_RET


def process_data_tpl(cfg):
    tpl_loc = cfg[DATA_TPL_FILE]
    tpl_data = {HEAD_CONTENT: [], ATOMS_CONTENT: [], TAIL_CONTENT: [], PROT_RES_MOL: [], H3O_MOL: [],
                WATER_MOLS: defaultdict(list), FIRST_H3O_H_INDEX: None}
    section = SEC_HEAD
    num_atoms_pat = re.compile(r"(\d+).*atoms$")
    atoms_pat = re.compile(r"^Atoms.*")
    # put in dummy x y z
    x = 0.0
    y = 0.0
    z = 0.0

    total_charge = 0.0

    # For debugging total charge
    calc_charge_atom_nums = {}
    for name in CALC_CHARGE_NAMES:
        calc_charge_atom_nums[cfg[name]] = name

    with open(tpl_loc) as f:
        for line in f:
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
            # atoms_content to contain everything but the xyz: atom_num, mol_num, atom_type, charge, type'
            elif section == SEC_ATOMS:
                if len(line) == 0:
                    continue
                split_line = line.split()
                atom_num = int(split_line[0])
                mol_num = int(split_line[1])
                atom_type = int(split_line[2])
                charge = float(split_line[3])
                description = ' '.join(split_line[7:])
                atom_struct = [atom_num, mol_num, atom_type, charge, x, y, z, description]
                tpl_data[ATOMS_CONTENT].append(atom_struct)
                total_charge += charge

                if atom_type == cfg[H3O_O_TYPE]:
                    tpl_data[H3O_MOL].append(atom_struct)
                    tpl_data[H3O_O_CHARGE] = charge
                elif atom_type == cfg[H3O_H_TYPE]:
                    if tpl_data[FIRST_H3O_H_INDEX] is None:
                        tpl_data[FIRST_H3O_H_INDEX] = len(tpl_data[H3O_MOL])
                    tpl_data[H3O_MOL].append(atom_struct)
                    tpl_data[H3O_H_CHARGE] = charge
                elif mol_num == cfg[PROT_RES_MOL_ID]:
                    tpl_data[PROT_RES_MOL].append(atom_struct)
                elif atom_type == cfg[WAT_O_TYPE] or atom_type == cfg[WAT_H_TYPE]:
                    tpl_data[WATER_MOLS][mol_num].append(atom_struct)
                if atom_num == tpl_data[NUM_ATOMS]:
                    section = SEC_TAIL
                    ## Perform checks total charge
                    if abs(total_charge) < TOL:
                        print('The data file system is neutral (total charge {:.2e})'.format(total_charge))
                    else:
                        warning('The data file system is not neutral. Total charge {0:.6f}'.format(total_charge))
                    if len(tpl_data[PROT_RES_MOL]) == 0:
                        raise InvalidDataError('Did not find the input {} ({}).'.format(PROT_RES_MOL,
                                                                                        cfg[PROT_RES_MOL]))
                    for mol_list in [H3O_MOL, WATER_MOLS]:
                        if len(tpl_data[mol_list]) == 0:
                            raise InvalidDataError('In reading the data file, found no {}. Check the data file and '
                                                   'the input atom types: \n{} = {}\n{} = {}\n{} = {}\n'
                                                   '{} = {}\n{} = {}.'
                                                   ''.format(mol_list,
                                                             PROT_H_TYPE, cfg[PROT_H_TYPE],
                                                             H3O_O_TYPE, cfg[H3O_O_TYPE],
                                                             H3O_H_TYPE, cfg[H3O_H_TYPE],
                                                             WAT_O_TYPE, cfg[WAT_O_TYPE],
                                                             WAT_H_TYPE, cfg[WAT_H_TYPE]))

                elif atom_num in calc_charge_atom_nums:
                    print('After atom {0} ({1}), the total charge is: {2:.3f}'.format(atom_num,
                                                                                      calc_charge_atom_nums[atom_num],
                                                                                      total_charge))

            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                tpl_data[TAIL_CONTENT].append(line)

    # Validate data section
    if len(tpl_data[ATOMS_CONTENT]) != tpl_data[NUM_ATOMS]:
        raise InvalidDataError('In the file {}, The length of the "Atoms" section ({}) does not equal '
                               'the number of atoms ({}).'.format(tpl_loc,
                                                                  len(tpl_data[ATOMS_CONTENT]),
                                                                  tpl_data[NUM_ATOMS]))

    if cfg[REPROD_TPL]:
        f_out = create_out_fname('reproduced_tpl', base_dir=cfg[OUT_BASE_DIR], ext='.data')
        list_to_file(tpl_data[HEAD_CONTENT] + tpl_data[ATOMS_CONTENT][:] + tpl_data[TAIL_CONTENT],
                     f_out)
        print('Wrote file: {}'.format(f_out))

    return tpl_data


def deprotonate(cfg, protonatable_res, excess_proton, dump_h3o_mol, water_mol_dict, box, tpl_data):
    """
    Deprotonate a the residue and assign the proton to the closest water
    so that the output data matches with the template.
    """
    # Convert excess proton to a hydronium proton
    excess_proton[1] = tpl_data[H3O_MOL][0][1]   # molecule number
    excess_proton[2] = cfg[H3O_H_TYPE]           # type
    excess_proton[3] = tpl_data[H3O_H_CHARGE]    # charge
    dump_h3o_mol.append(excess_proton)
    min_dist_id = None
    min_dist = np.linalg.norm(box)
    for mol_id, molecule in water_mol_dict.items():
        for atom in molecule:
            if atom[2] == cfg[WAT_O_TYPE]:
                dist = pbc_dist(np.asarray(excess_proton[4:7]), np.asarray(atom[4:7]), box)
        if dist < min_dist:
            min_dist_id = mol_id
            min_dist = dist
    logger.debug('Deprotonated residue: the molecule ID of the closest water '
                 '(to become a hydronium) is %s.', min_dist_id)
    # Now that have the closest water, add its atoms to the hydronium list
    for atom in water_mol_dict[min_dist_id]:
        dump_h3o_mol.append(atom)
        # Remove the closest water from the dictionary of water molecules, and convert it to a hydronium
    del water_mol_dict[min_dist_id]
    for atom in dump_h3o_mol:
        if atom[2] == cfg[WAT_O_TYPE]:
            atom[2] = cfg[H3O_O_TYPE]
            atom[3] = tpl_data[H3O_O_CHARGE]
        elif atom[2] == cfg[WAT_H_TYPE]:
            atom[2] = cfg[H3O_H_TYPE]
            atom[3] = tpl_data[H3O_H_CHARGE]
    # Make the atom type and charge of the protonatable residue the same as for the template file (switching
    # from protonated to deprotonated residue)
    if len(tpl_data[PROT_RES_MOL]) != len(protonatable_res):
        raise InvalidDataError('Encountered dump file in which the number of atoms in the '
                               'protonatable residue does not equal the number of atoms in the template data file.')


def sort_wat_mols(cfg, water_dict):
    """
    Sorts waters molecules
    @param cfg: configuration for run. Used for getting atom types.
    @param water_dict: dictionary of water atoms by molecule key
    @return: a list that is ordered so all water atoms appear consecutively, oxygen first.
    """
    wat_list = []
    for mol in water_dict:
        h_atoms = []
        # to make sure oxygen first, add it, then hydrogen atoms
        for atom in water_dict[mol]:
            if atom[2] == cfg[WAT_O_TYPE]:
                wat_list.append(atom)
            else:
                h_atoms.append(atom)
        for atom in h_atoms:
            wat_list.append(atom)
    return wat_list


def assign_hyd_mol(cfg, hyd_mol):
    ordered_hyd_mol = []
    h_atoms = []
    for atom in hyd_mol:
        if atom[2] == cfg[H3O_O_TYPE]:
            ordered_hyd_mol.append(atom)
        else:
            h_atoms.append(atom)
    for atom in h_atoms:
        ordered_hyd_mol.append(atom)
    return ordered_hyd_mol


def process_dump_file(cfg, data_tpl_content, dump_file):
    section = None
    box = np.zeros((3,))
    counter = 1
    atom_list_order = [PRE_RES, PROT_RES, POST_RES, HYD_MOL, WAT_MOL, POST_WAT]
    dump_atom_data = []
    atom_lists = {PRE_RES: [],
                  PROT_RES: [],
                  POST_RES: [],
                  HYD_MOL: [],
                  WAT_MOL: [],
                  POST_WAT: []
                  }

    with open(dump_file) as d:
        for line in d:
            line = line.strip()
            if section is None:
                section = find_dump_section_state(line)
                #logger.debug("In process_dump_files, set section to %s.", section)
                if section is None:
                    raise InvalidDataError('Unexpected line in file {}: {}'.format(dump_file, line))
            elif section == SEC_TIMESTEP:
                timestep = line
                # Reset variables
                water_dict = defaultdict(list)
                dump_atom_data = []
                excess_proton = None
                hydronium = []
                for a_list in atom_lists:
                    atom_lists[a_list] = []
                section = None
            elif section == SEC_NUM_ATOMS:
                if data_tpl_content[NUM_ATOMS] != int(line):
                    raise InvalidDataError('At timestep {} in file {}, the listed number of atoms ({}) does '
                                           'not equal the number of atoms in the template data file '
                                           '({}).'.format(timestep, dump_file, line, data_tpl_content[NUM_ATOMS]))
                section = None
            elif section == SEC_BOX_SIZE:
                split_line = line.split()
                diff = float(split_line[1]) - float(split_line[0])
                box[counter - 1] = diff
                if counter == 3:
                    counter = 0
                    section = None
                counter += 1
            elif section == SEC_ATOMS:
                split_line = line.split()
                # If there is an incomplete line in a dump file, move on to the next file
                if len(split_line) < 7:
                    continue
                atom_num = int(split_line[0])
                mol_num = int(split_line[1])
                atom_type = int(split_line[2])
                charge = float(split_line[3])
                x, y, z = map(float, split_line[4:7])
                description = ''
                atom_struct = [atom_num, mol_num, atom_type, charge, x, y, z, description]

                # Keep track of separate portions of the system to allow sorting and processing
                if mol_num == cfg[PROT_RES_MOL_ID]:
                    if atom_type == cfg[PROT_H_TYPE] and atom_num not in cfg[PROT_H_IGNORE]:
                        excess_proton = atom_struct
                    else:
                        atom_lists[PROT_RES].append(atom_struct)
                elif atom_type == cfg[H3O_O_TYPE] or atom_type == cfg[H3O_H_TYPE]:
                    hydronium.append(atom_struct)
                elif atom_type == cfg[WAT_O_TYPE] or atom_type == cfg[WAT_H_TYPE]:
                    water_dict[mol_num].append(atom_struct)
                # Save everything else in three chunks for recombining sections post-processing
                elif len(atom_lists[PROT_RES]) == 0:
                    atom_lists[PRE_RES].append(atom_struct)
                elif len(water_dict) == 0:
                    atom_lists[POST_RES].append(atom_struct)
                else:
                    atom_lists[POST_WAT].append(atom_struct)

                if counter == data_tpl_content[NUM_ATOMS]:
                    counter = 0
                    section = None

                    # Now that finished reading all atom lines...
                    # Check and process!
                    if len(water_dict) == 0:
                        raise InvalidDataError('Found no water molecules. Check that the input types {} = {} '
                                               'and {} = {} are in the dump '
                                               'file.'.format(WAT_O_TYPE, cfg[WAT_O_TYPE],
                                                              WAT_H_TYPE, cfg[WAT_H_TYPE]))
                    if excess_proton is None:
                        if len(hydronium) != 4:
                            raise InvalidDataError('Did not find an excess proton or one hydronium ion. Check dump '
                                                   'file and input types: {} = {}; {} = {}; {} = {}'
                                                   .format(PROT_H_TYPE, cfg[PROT_H_TYPE],
                                                           H3O_O_TYPE, cfg[H3O_O_TYPE],
                                                           H3O_H_TYPE, cfg[H3O_H_TYPE]))
                    else:
                        if len(hydronium) != 0:
                            raise InvalidDataError('Found an excess proton and a hydronium atoms. Check dump file '
                                                   'and input types: {} = {}; {} = {}; {} = {}'
                                                   .format(PROT_H_TYPE, cfg[PROT_H_TYPE],
                                                           H3O_O_TYPE, cfg[H3O_O_TYPE],
                                                           H3O_H_TYPE, cfg[H3O_H_TYPE]))
                        deprotonate(cfg, atom_lists[PROT_RES], excess_proton, hydronium,
                                    water_dict, box, data_tpl_content)

                    # Ensure in correct order for printing
                    atom_lists[HYD_MOL] = assign_hyd_mol(cfg, hydronium)
                    atom_lists[WAT_MOL] = sort_wat_mols(cfg, water_dict)

                    for a_list in atom_list_order:
                        dump_atom_data += atom_lists[a_list]

                    # overwrite atom_num, mol_num, atom_type, charge, then description
                    for index in range(len(dump_atom_data)):
                        if dump_atom_data[index][3] == data_tpl_content[ATOMS_CONTENT][index][3] or \
                                dump_atom_data[index][0] in cfg[PROT_TYPE_IGNORE_ATOMS]:
                            dump_atom_data[index][0:4] = data_tpl_content[ATOMS_CONTENT][index][0:4]
                            dump_atom_data[index][7] = ' '.join(data_tpl_content[ATOMS_CONTENT][index][7:])
                        else:
                            raise InvalidDataError("In reading file: {}\n found atom index {} with charge {} which "
                                                   "does not match the charge in the data template ({}). \n"
                                                   "To ignore this mis-match, list "
                                                   "the atom's index number in the keyword '{}' in the ini file."
                                                   "".format(dump_file,
                                                             dump_atom_data[index][0], dump_atom_data[index][3],
                                                             data_tpl_content[ATOMS_CONTENT][index][3],
                                                             PROT_TYPE_IGNORE_ATOMS))

                    d_out = create_out_fname(dump_file, suffix='_' + str(timestep),
                                             ext='.data', base_dir=cfg[OUT_BASE_DIR])
                    data_tpl_content[HEAD_CONTENT][0] = "Created by evbdump2data from {} " \
                                                        "timestep {}".format(dump_file, timestep)
                    list_to_file(data_tpl_content[HEAD_CONTENT] + dump_atom_data + data_tpl_content[TAIL_CONTENT],
                                 d_out)
                    print('Wrote file: {}'.format(d_out))
                counter += 1
    if counter == 1:
        print("Completed reading dumpfile {}".format(dump_file))
    else:
        warning("Dump file {} step {} did not have the full list of atom numbers. "
                "Continuing program.".format(dump_file, timestep))


def process_dump_files(cfg, data_tpl_content):
    with open(cfg[DUMPS_FILE]) as f:
        for dump_file in f:
            dump_file = dump_file.strip()
            # ignore blank lines in dump file list
            if len(dump_file) == 0:
                continue
            else:
                process_dump_file(cfg, data_tpl_content, dump_file)


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    # Read template and dump files
    cfg = args.config
    try:
        data_tpl_content = process_data_tpl(cfg)
        process_dump_files(cfg, data_tpl_content)
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
