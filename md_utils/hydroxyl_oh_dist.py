#!/usr/bin/env python
"""
From a dump file, finds the hydroxyl OH distance on the protonateable residue (when protonated)
"""

from __future__ import print_function

import ConfigParser
import logging
import re
import numpy as np
from md_utils.md_common import list_to_file, InvalidDataError, create_out_suf_fname, to_int_list, pbc_dist, warning, conv_raw_val

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

# Defaults
DEF_CFG_FILE = 'hydroxyl_oh_dist.ini'
# Set notation
DEF_CFG_VALS = {DUMPS_FILE: 'list.txt', PROT_IGNORE: [], PROT_O_IDS: [], }
REQ_KEYS = {PROT_RES_MOL_ID: int, PROT_H_TYPE: int, }

# For dump file processing
SEC_TIMESTEP = 'timestep'
SEC_NUM_ATOMS = 'dump_num_atoms'
SEC_BOX_SIZE = 'dump_box_size'
SEC_ATOMS = 'atoms_section'


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
    parser = argparse.ArgumentParser(description='Find difference of distances between carboxylic oxygens and '
                                                 'the excess proton, if the carboxylic group is protonated. '
                                                 'Currently, this script expects only one '
                                                 'protonatable residue.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "See the example file /test/test_data/evbd2d/lammps_dist_pbc.ini. "
                                               "The default file name is lammps_dist_pbc.ini, located in the "
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


def find_section_state(line):
    atoms_pat = re.compile(r"^ITEM: ATOMS id mol type q x y z.*")
    if line == 'ITEM: TIMESTEP':
        return SEC_TIMESTEP
    elif line == 'ITEM: NUMBER OF ATOMS':
        return SEC_NUM_ATOMS
    elif line == 'ITEM: BOX BOUNDS pp pp pp':
        return SEC_BOX_SIZE
    elif atoms_pat.match(line):
        return SEC_ATOMS


def calc_dists(excess_proton, carboxy_oxys,box):
    if excess_proton is None:
        return 'nan,nan,nan'
    else:
        dist = {}
        for index,atom in enumerate(carboxy_oxys):
            dist[index] = pbc_dist(np.asarray(excess_proton[4:7]), np.asarray(atom[4:7]), box)
        return ','.join(map(str,[dist[0], dist[1], abs(dist[0] - dist[1])]))


def process_dump_files(cfg):
    """
    @param cfg: configuration data read from ini file
    @return: @raise InvalidDataError:
    """
    with open(cfg[DUMPS_FILE]) as f:
        for dump_file in f.readlines():
            dump_file = dump_file.strip()
            with open(dump_file) as d:
                section = None
                box = np.zeros((3,))
                counter = 1
                dist_diffs = ['timestep,oh_dist1,oh_dist2,dist_diff']
                for line in d.readlines():
                    line = line.strip()
                    if section is None:
                        section = find_section_state(line)
                        #logger.debug("In process_dump_files, set section to %s.", section)
                        if section is None:
                            raise InvalidDataError('Unexpected line in file {}: {}'.format(d, line))
                    elif section == SEC_TIMESTEP:
                        timestep = line
                        # Reset variables
                        # Start with an entry so the atom-id = index
                        dump_atom_data = ['']
                        carboxy_oxys = []
                        excess_proton = None
                        section = None
                    elif section == SEC_NUM_ATOMS:
                        num_atoms = int(line)
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
                        atom_num = int(split_line[0])
                        mol_num = int(split_line[1])
                        atom_type = int(split_line[2])
                        charge = float(split_line[3])
                        x, y, z = map(float, split_line[4:7])
                        # Here, the atoms counting starts at 1. However, the template counted from zero
                        atom_struct = [atom_num, mol_num, atom_type, charge, x, y, z]
                        dump_atom_data.append(atom_struct)
                        # Keep track of carboxylic oxygens.
                        if mol_num == cfg[PROT_RES_MOL_ID]:
                            if atom_num in cfg[PROT_O_IDS]:
                                carboxy_oxys.append(atom_struct)
                            elif (atom_type == cfg[PROT_H_TYPE]) and (atom_num not in cfg[PROT_IGNORE]):
                                excess_proton = atom_struct
                        if counter == num_atoms:
                            counter = 0
                            if len(carboxy_oxys) == 2:
                                dist_diffs.append(timestep+','+calc_dists(excess_proton,carboxy_oxys,box))
                            else:
                                raise InvalidDataError('Expected to find atom indices {} in resid {} (to be treated as '
                                                       'carboxylic oxygens). Found {} such indices at timestep {}. '
                                                       'Check input data.'.format(cfg[PROT_O_IDS],cfg[PROT_RES_MOL_ID],
                                                                len(carboxy_oxys),timestep))
                            section = None
                        counter += 1
                # Now that finished reading all atom lines...
            #print(dist_diffs)

            d_out = create_out_suf_fname(dump_file, '_oh_dist', ext='.csv')
            list_to_file(dist_diffs, d_out)
            print('Wrote file: {}'.format(d_out))
    return


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    # TODO: did not show the expected behavior when I didn't have a required cfg in the ini file
    if ret != GOOD_RET:
        return ret

    # TODO: in generated data files, print atom types and provide new header based on where this came from

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
