#!/usr/bin/env python
"""
From a dump file, finds the hydroxyl OH distance on the protonateable residue (when protonated)
"""

from __future__ import print_function

import ConfigParser
import logging
import numpy as np
from md_utils.md_common import list_to_file, InvalidDataError, create_out_suf_fname, pbc_dist, warning, process_cfg, find_dump_section_state, write_csv

import sys
import argparse


__author__ = 'hmayes'


# Logging
logger = logging.getLogger('hydroxyl_oh_dist')
logging.basicConfig(filename='hydroxyl_oh_dist.log', filemode='w', level=logging.DEBUG)
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
DUMPS_FILE = 'dump_list_file'

PROT_RES_MOL_ID = 'prot_res_mol_id'
PROT_H_TYPE = 'prot_h_type'
PROT_IGNORE = 'prot_ignore_atom_nums'
PROT_O_IDS = 'prot_carboxy_oxy_atom_nums'
OUT_BASE_DIR = 'output_directory'

# Defaults
DEF_CFG_FILE = 'hydroxyl_oh_dist.ini'
# Set notation
DEF_CFG_VALS = {DUMPS_FILE: 'list.txt',
                PROT_IGNORE: [],
                PROT_O_IDS: [],
                OUT_BASE_DIR: None,
                }
REQ_KEYS = {PROT_RES_MOL_ID: int,
            PROT_H_TYPE: int,
            }

# For dump file processing
SEC_TIMESTEP = 'timestep'
SEC_NUM_ATOMS = 'dump_num_atoms'
SEC_BOX_SIZE = 'dump_box_size'
SEC_ATOMS = 'atoms_section'
ATOM_NUM = 'atom_num'
MOL_NUM = 'mol_num'
ATOM_TYPE = 'atom_type'
CHARGE = 'charge'
XYZ_COORDS = 'x,y,z'

# Values to output
TIMESTEP = 'timestep'
OH_MIN = 'oh_min'
OH_MAX = 'oh_max'
OH_DIFF = 'oh_diff'
OUT_FIELDNAMES = [TIMESTEP, OH_MIN, OH_MAX, OH_DIFF]

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
    parser = argparse.ArgumentParser(description='Find difference of distances between carboxylic oxygens and '
                                                 'the excess proton, if the carboxylic group is protonated. '
                                                 'Currently, this script expects only one '
                                                 'protonatable residue.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run. The required keys are: {}".format(DEF_CFG_FILE, REQ_KEYS.keys()),
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


def calc_OH_dists(excess_proton, carboxy_oxys, box):
    if excess_proton is None:
        return {OH_MIN: 'nan', OH_MAX: 'nan', OH_DIFF: 'nan'}
    else:
        dist = np.zeros(2)
        for index,atom in enumerate(carboxy_oxys):
            dist[index] = pbc_dist(np.asarray(excess_proton[XYZ_COORDS]), np.asarray(atom[XYZ_COORDS]), box)
        return {OH_MIN: np.amin(dist),
                OH_MAX: np.amax(dist),
                OH_DIFF:  abs(dist[0] - dist[1])}


def process_atom_data(cfg, dump_atom_data, box, timestep):
    carboxy_oxys = []
    excess_proton = None
    results = {}
    for atom in dump_atom_data:
        # Keep track of carboxylic oxygens.
        if atom[MOL_NUM] == cfg[PROT_RES_MOL_ID]:
            if atom[ATOM_NUM] in cfg[PROT_O_IDS]:
                carboxy_oxys.append(atom)
            elif (atom[ATOM_TYPE] == cfg[PROT_H_TYPE]) and ( atom[ATOM_NUM] not in cfg[PROT_IGNORE]):
                excess_proton = atom
    if len(carboxy_oxys) == 2:
        return calc_OH_dists(excess_proton,carboxy_oxys,box)
    else:
        raise InvalidDataError('Expected to find atom indices {} in resid {} (to be treated as '
                               'carboxylic oxygens). Found {} such indices at timestep {}. '
                               'Check input data.'.format(cfg[PROT_O_IDS],cfg[PROT_RES_MOL_ID],
                                        len(carboxy_oxys),timestep))

def read_dump_file(dump_file, cfg, data_to_print):
    with open(dump_file) as d:
        section = None
        box = np.zeros((3,))
        box_counter = 1
        atom_counter = 1
        dist_diffs = ['timestep,oh_dist1,oh_dist2,dist_diff']
        for line in d.readlines():
            line = line.strip()
            if section is None:
                section = find_dump_section_state(line)
                #logger.debug("In process_dump_files, set section to %s.", section)
                if section is None:
                    raise InvalidDataError('Unexpected line in file {}: {}'.format(d, line))
            elif section == SEC_TIMESTEP:
                timestep = line
                # Reset variables
                dump_atom_data = []
                result = { TIMESTEP: timestep }
                section = None
            elif section == SEC_NUM_ATOMS:
                num_atoms = int(line)
                section = None
            elif section == SEC_BOX_SIZE:
                split_line = line.split()
                diff = float(split_line[1]) - float(split_line[0])
                box[box_counter - 1] = diff
                if box_counter == 3:
                    box_counter = 0
                    section = None
                box_counter += 1
            elif section == SEC_ATOMS:
                split_line = line.split()
                atom_num = int(split_line[0])
                mol_num = int(split_line[1])
                atom_type = int(split_line[2])
                charge = float(split_line[3])
                x, y, z = map(float, split_line[4:7])
                # Here, the atoms counting starts at 1. However, the template counted from zero
                atom_struct = {ATOM_NUM: atom_num,
                               MOL_NUM: mol_num,
                               ATOM_TYPE: atom_type,
                               CHARGE: charge,
                               XYZ_COORDS: [x,y,z], }
                dump_atom_data.append(atom_struct)
                if atom_counter == num_atoms:
                    result.update(process_atom_data(cfg, dump_atom_data, box, timestep))
                    print(result)
                    data_to_print.append(result)
                    atom_counter = 0
                    section = None
                atom_counter += 1


def process_dump_files(cfg):
    """
    @param cfg: configuration data read from ini file
    """
    data_to_print = []
    with open(cfg[DUMPS_FILE]) as f:
        for dump_file in f.readlines():
            dump_file = dump_file.strip()
            read_dump_file(dump_file, cfg, data_to_print)

            #print(dist_diffs)
    f_out = create_out_suf_fname(dump_file, '_oh_dist', ext='.csv', base_dir=cfg[OUT_BASE_DIR])
    write_csv(data_to_print, f_out, OUT_FIELDNAMES)
    print('Wrote file: {}'.format(f_out))

    return


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET:
        return ret

    # Read template and dump files
    cfg = args.config
    try:
        process_dump_files(cfg)
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
