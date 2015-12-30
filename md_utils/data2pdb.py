#!/usr/bin/env python
"""
Creates lammps data files from lammps dump files, given a template lammps data file.
"""

from __future__ import print_function

import ConfigParser
from collections import defaultdict
import copy
import logging
import re
import numpy as np
import csv
from md_utils.md_common import list_to_file, InvalidDataError, seq_list_to_file, create_out_suf_fname

import sys
import argparse

__author__ = 'mayes'


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
DATAS_FILE = 'data_list_file'
# PDB file info
PDB_ATOM_INFO_LAST_CHAR = 'pdb_atom_info_last_char'
PDB_MOL_NUM_LAST_CHAR = 'pdb_mol_num_last_char'
PDB_X_LAST_CHAR = 'pdb_x_last_char'
PDB_Y_LAST_CHAR = 'pdb_y_last_char'
PDB_Z_LAST_CHAR = 'pdb_z_last_char'
PDB_FORMAT = 'pdb_print_format'
# data file info
WAT_O_TYPE = 'water_o_type'
WAT_H_TYPE = 'water_h_type'
H3O_O_TYPE = 'h3o_o_type'
H3O_H_TYPE = 'h3o_h_type'

# Defaults
DEF_CFG_FILE = 'data2pdb.ini'
# Set notation
DEF_CFG_VALS = {DATAS_FILE: 'data_list.txt', PDB_FORMAT: '%s%4d    %8.3f%8.3f%8.3f%s', }
REQ_KEYS = {PDB_TPL_FILE: str, WAT_O_TYPE: int, WAT_H_TYPE: int, H3O_O_TYPE: int, H3O_H_TYPE: int,
            PDB_ATOM_INFO_LAST_CHAR: int, PDB_MOL_NUM_LAST_CHAR: int,
            PDB_X_LAST_CHAR: int, PDB_Y_LAST_CHAR: int, PDB_Z_LAST_CHAR: int, }

# From data template file
NUM_ATOMS = 'num_atoms'
HEAD_CONTENT = 'head_content'
ATOMS_CONTENT = 'atoms_content'
TAIL_CONTENT = 'tail_content'

# For data template file processing
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'

def warning(*objs):
    """Writes a message to stderr."""
    print("WARNING: ", *objs, file=sys.stderr)


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
    parser = argparse.ArgumentParser(description='Creates pdb files from lammps data, given a template pdb file.'
                                                 'The required input file provides the location of the '
                                                 'template file, a file with a list of data files to convert, and '
                                                 'information about the configuration of the data file to allow for '
                                                 'some checks on the data files.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini "
                                               "format. See the example file /test/test_data/pdb2data/pdb2data.ini. "
                                               "The default file name is pdb2data.ini, located in the "
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


def pdb_atoms_to_file(pdb_format, list_val, fname, mode='w'):
    """
    Writes the list of sequences to the given file in the specified format for a PDB.

    :param list_val: The list of sequences to write.
    :param fname: The location of the file to write.
    """
    with open(fname, mode) as myfile:
        for line in list_val:
            #print(pdb_format % tuple(line))
            myfile.write(pdb_format % tuple(line) + '\n')


def process_pdb_tpl(cfg):
    tpl_loc = cfg[PDB_TPL_FILE]
    tpl_data = {}
    tpl_data[HEAD_CONTENT] = []
    tpl_data[ATOMS_CONTENT] = []
    tpl_data[TAIL_CONTENT] = []
    section = SEC_HEAD
    end_pat = re.compile(r"^END.*")
    print_me = 0
    with open(tpl_loc) as f:
        for line in f.readlines():
            line = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                tpl_data[HEAD_CONTENT].append(line)
                section = SEC_ATOMS
            # atoms_content to contain everything but the xyz
            elif section == SEC_ATOMS:
                if end_pat.match(line):
                    section = SEC_TAIL
                    tpl_data[TAIL_CONTENT].append(line)
                    continue
                # tpl_data[ATOMS_CONTENT].append(line)

                first_cols = line[:cfg[PDB_ATOM_INFO_LAST_CHAR]]
                # TODO: check with Chris: I was going to put a try here (both for making int and float); not needed?
                # There is already a try when calling the subroutine, so maybe I don't need to?
                mol_num = int(line[cfg[PDB_ATOM_INFO_LAST_CHAR]:cfg[PDB_MOL_NUM_LAST_CHAR]])
                pdb_x = float(line[cfg[PDB_MOL_NUM_LAST_CHAR]:cfg[PDB_X_LAST_CHAR]])
                pdb_y = float(line[cfg[PDB_X_LAST_CHAR]:cfg[PDB_Y_LAST_CHAR]])
                pdb_z = float(line[cfg[PDB_Y_LAST_CHAR]:cfg[PDB_Z_LAST_CHAR]])
                last_cols = line[cfg[PDB_Z_LAST_CHAR]:]
                line_struct = [first_cols, mol_num, pdb_x, pdb_y, pdb_z, last_cols]
                tpl_data[ATOMS_CONTENT].append(line_struct)
            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                tpl_data[TAIL_CONTENT].append(line)

    if logger.isEnabledFor(logging.DEBUG):
        list_to_file(tpl_data[HEAD_CONTENT], 'reproduced_tpl.pdb')
        pdb_atoms_to_file(cfg[PDB_FORMAT], tpl_data[ATOMS_CONTENT], 'reproduced_tpl.pdb', mode='a')
        list_to_file(tpl_data[TAIL_CONTENT], 'reproduced_tpl.pdb', mode='a')

    return tpl_data


def find_section_state(line):
    # atoms_pat = re.compile(r"^ITEM: ATOMS id mol type q x y z.*")
    # if line == 'ITEM: TIMESTEP':
    #     return SEC_TIMESTEP
    # elif line == 'ITEM: NUMBER OF ATOMS':
    #     return SEC_NUM_ATOMS
    # elif line == 'ITEM: BOX BOUNDS pp pp pp':
    #     return SEC_BOX_SIZE
    # elif atoms_pat.match(line):
    #     return SEC_ATOMS
    pass


def pbc_dist(a, b, box):
    dist = a - b
    dist = dist - box * np.asarray(map(round, dist / box))
    return np.linalg.norm(dist)


def process_dump_atoms(cfg, protonatable_res, excess_proton, dump_h3o_mol, water_mol_dict, box, tpl_data):
    """
    Correct for any reordering and residue protonation that may have happened in the course of the simulation,
    so that the output data matches with the template.
    """
    # first, if the residue is protonated, remove the excess proton from the residue and make sure a hydronium
    if len(dump_h3o_mol) == 0:
        # Convert excess proton to a hydronium proton
        # excess_proton[1] = tpl_data[H3O_MOL][0][1]
        # excess_proton[2] = cfg[H3O_H_TYPE]
        # excess_proton[3] = tpl_data[H3O_H_CHARGE]
        dump_h3o_mol.append(excess_proton)
        min_dist = np.linalg.norm(box)
        for mol_id, molecule in water_mol_dict.items():
            for atom in molecule:
                if atom[2] == cfg[WAT_O_TYPE]:
                    dist = pbc_dist(np.asarray(excess_proton[4:]), np.asarray(atom[4:]), box)
            if dist < min_dist:
                min_dist_id = mol_id
                min_dist = dist
                # Now that have the closed water, add its atoms to the hydronium list
                # logger.debug("In deprotonating residue routine, the molecule ID of the closest water (to become a hydronium)"
            #              "is %s.", min_dist_id)
        for atom in water_mol_dict[min_dist_id]:
            dump_h3o_mol.append(atom)
            # Remove the closest water from the dictionary of water molecules, and convert it to a hydronium
        del water_mol_dict[min_dist_id]
        # for atom in dump_h3o_mol:
        #     if atom[2] == cfg[WAT_O_TYPE]:
        #         atom[2] = cfg[H3O_O_TYPE]
        #         atom[3] = tpl_data[H3O_O_CHARGE]
        #     elif atom[2] == cfg[WAT_H_TYPE]:
        #         atom[2] = cfg[H3O_H_TYPE]
        #         atom[3] = tpl_data[H3O_H_CHARGE]
        #         # Make the atom type and charge of the protonatable residue the same as for the template file (switching
        #         # from protonated to deprotonated residue)
        # if len(tpl_data[PROT_RES_MOL]) != len(protonatable_res):
        #     raise InvalidDataError('In the current timestep of the current dump file, the number of atoms in the ' \
        #                            'protonatable residue does not equal the number of atoms in the template data file.')
        # for atom in range(0, len(protonatable_res)):
        #     if protonatable_res[atom][0:2] == tpl_data[PROT_RES_MOL][atom][0:2]:
        #         protonatable_res[atom][2:4] = tpl_data[PROT_RES_MOL][atom][2:4]
        #     else:
        #         raise InvalidDataError('In the current timestep of the current dump file, the atoms in the ' \
        #                                'protonatable residue are not ordered as in the template data file.')


    #  if the h3o molecule id does not match the template, make it so
    # Note: assumed excess proton is the first element in the h3o
    # saved as new name for readability only
    # target_h3o_mol_id = tpl_data[H3O_MOL][-1][1]
    # Note: if the procedure for deprotonating a residue has been run, (at least currently) the first hydrogen may
    # have the correct molecule ID, while the rest does not! Thus, check from the last atom of the molecule
    # (guaranteed not to be the first hydrogen!)
    # if dump_h3o_mol[-1][1] != target_h3o_mol_id:
    #     new_h3o_mol = []
    #     new_water_mol = []
    #     # FYI on why I used copy: I was assigning parts of the original water and h3o to the same new molecules,
    #     # and it was referencing only, so I did not get my required combination results. Fixed now.
    #     water_props = copy.deepcopy(water_mol_dict[target_h3o_mol_id])
    #     for atom_id, atom in enumerate(dump_h3o_mol):
    #         # Grab a hydrogen. tpl_data[FIRST_H3O_H_INDEX] can only be 0 or 1.
    #         if atom_id == tpl_data[FIRST_H3O_H_INDEX]:
    #             # double check really is a hydrogen
    #             if atom[2] == cfg[H3O_H_TYPE]:
    #                 atom[1] = target_h3o_mol_id
    #                 new_h3o_mol = [atom] + water_mol_dict[target_h3o_mol_id]
    #             else:
    #                 # TODO: Take care of possible problem?
    #                 raise InvalidDataError('In the current timestep of the current dump file, there was an ' \
    #                                        'oxygen where a hydrogen was expected. Please fix the code to handle this problem!')
    #         else:
    #             new_water_mol.append(atom)
    #             new_h3o_mol[atom_id][2:] = copy.copy(atom[2:])
    #     for atom_id, atom in enumerate(new_water_mol):
    #         atom[2:] = water_props[atom_id][2:]
    #     del water_mol_dict[target_h3o_mol_id]
    #     water_mol_dict[new_water_mol[0][1]] = copy.copy(new_water_mol)

    # TODO: Return here: Reorder water molecules if needed
    # if the order of the water atoms does not match the template, make it so!
    # if len(tpl_data[WATER_MOLS]) != len(water_mol_dict):
    #     raise InvalidDataError('In the current timestep of the current dump file, the number water atoms ' \
    #                            'does not equal the number of atoms in the template data file.')
    # for mol_id, molecule in water_mol_dict.items():
    #     for atom_id, atom in enumerate(molecule):
    #         # print(tpl_data[WATER_MOLS])
    #         if atom[0] == tpl_data[WATER_MOLS][mol_id][atom_id][0] and \
    #                       atom[2] == tpl_data[WATER_MOLS][mol_id][atom_id][2]:
    #             break
    #         print('Fix me!', atom, tpl_data[WATER_MOLS][mol_id][atom_id])
    return


def process_dump_files(cfg, data_tpl_content):
    section = None
    box = np.zeros((3,))
    with open(cfg[DATAS_FILE]) as f:
        for dump_file in f.readlines():
            dump_file = dump_file.strip()
            data_file_num = 0
            with open(dump_file) as d:
                counter = 1
                for line in d.readlines():
                    line = line.strip()
                    if section is None:
                        section = find_section_state(line)
                        #logger.debug("In process_dump_files, set section to %s.", section)
                        if section is None:
                            raise InvalidDataError('Unexpected line in file {}: {}'.format(d, line))
                    # elif section == SEC_TIMESTEP:
                    #     timestep = line
                    #     # Reset variables
                    #     water_dict = defaultdict(list)
                    #     dump_atom_data = []
                    #     excess_proton = None
                    #     h3o_mol = []
                    #     prot_res = []
                    #     data_file_num += 1
                    #     section = None
                    # elif section == SEC_NUM_ATOMS:
                    #     if data_tpl_content[NUM_ATOMS] != int(line):
                    #         raise InvalidDataError('At timestep {} in file {}, the listed number of atoms ({}) ' \
                    #                                'does not equal the number of atoms in the template data file ({}).'.format(
                    #             timestep, d, line, data_tpl_content[NUM_ATOMS]))
                    #     section = None
                    # elif section == SEC_BOX_SIZE:
                    #     split_line = line.split()
                    #     diff = float(split_line[1]) - float(split_line[0])
                    #     box[counter - 1] = diff
                    #     if counter == 3:
                    #         counter = 0
                    #         section = None
                    #     counter += 1
                    # elif section == SEC_ATOMS:
                    #     split_line = line.split()
                    #     atom_num = int(split_line[0])
                    #     mol_num = int(split_line[1])
                    #     atom_type = int(split_line[2])
                    #     charge = float(split_line[3])
                    #     x, y, z = map(float, split_line[4:7])
                    #     atom_struct = [atom_num, mol_num, atom_type, charge, x, y, z]
                    #     dump_atom_data.append(atom_struct)
                    #     # See if protonatable residue is protonated. If so, keep track of excess proton.
                    #     # Else, keep track of hydronium molecule.
                    #     if mol_num == cfg[PROT_RES_MOL_ID] and atom_type == cfg[PROT_H_TYPE] and atom_num not in cfg[
                    #         PROT_IGNORE]:
                    #         # subtract 1 from counter because counter starts at 1, index starts at zero
                    #         excess_proton = atom_struct
                    #     elif mol_num == cfg[PROT_RES_MOL_ID]:
                    #         prot_res.append(atom_struct)
                    #     elif atom_type == cfg[H3O_O_TYPE] or atom_type == cfg[H3O_H_TYPE]:
                    #         h3o_mol.append(atom_struct)
                    #     elif atom_type == cfg[WAT_O_TYPE] or atom_type == cfg[WAT_H_TYPE]:
                    #         water_dict[mol_num].append(atom_struct)
                    #     if counter == data_tpl_content[NUM_ATOMS]:
                    #         process_dump_atoms(cfg, prot_res, excess_proton, h3o_mol, water_dict, box, data_tpl_content)
                    #         d_out = create_out_suf_fname(dump_file, '_' + str(data_file_num), ext='.data')
                    #         list_to_file(data_tpl_content[HEAD_CONTENT], d_out)
                    #         seq_list_to_file(dump_atom_data, d_out, mode='a')
                    #         list_to_file(data_tpl_content[TAIL_CONTENT], d_out, mode='a')
                    #         print('Wrote file: {}'.format(d_out))
                    #         counter = 0
                    #         section = None
                    #     counter += 1
    return


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    # TODO: did not show the expected behavior when I didn't have a required cfg in the ini file
    if ret != GOOD_RET:
        return ret

    # Read template and dump files
    cfg = args.config
    try:
        pdb_tpl_content = process_pdb_tpl(cfg)
    #     process_dump_files(cfg, pdb_tpl_content)
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
