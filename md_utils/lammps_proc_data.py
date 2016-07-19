#!/usr/bin/env python
"""
From lammps dump file(s), finds key distance, such as:
CALC_OH_DIST: the hydroxyl OH distance on the protonatable residue (when protonated)

This script assumes we care about one protonatable residue in a simulation with a PBC
"""

from __future__ import print_function
# noinspection PyCompatibility
import ConfigParser
import logging
import os
import sys
import argparse

import numpy as np

from md_utils.md_common import InvalidDataError, create_out_fname, pbc_dist, warning, process_cfg, \
    find_dump_section_state, write_csv, list_to_csv, pbc_vector_avg

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('lammps_proc_data')
logging.basicConfig(filename='lammps_proc_data', filemode='w', level=logging.DEBUG)
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
DUMP_FILE_LIST = 'dump_list_file'
DUMP_FILE = 'dump_file'
PROT_RES_MOL_ID = 'prot_res_mol_id'
PROT_H_TYPE = 'prot_h_type'
PROT_H_IGNORE = 'prot_ignore_h_atom_nums'
PROT_O_IDS = 'prot_carboxyl_oxy_atom_nums'
WAT_O_TYPE = 'water_o_type'
WAT_H_TYPE = 'water_h_type'
H3O_O_TYPE = 'h3o_o_type'
H3O_H_TYPE = 'h3o_h_type'
GOFR_TYPE1 = 'gofr_type1'
GOFR_TYPE2 = 'gofr_type2'
OUT_BASE_DIR = 'output_directory'

# Types of calculations allowed
# g(r) types
CALC_HO_GOFR = 'calc_hstar_owat_gofr_flag'
CALC_OO_GOFR = 'calc_ostar_owat_gofr_flag'
CALC_HH_GOFR = 'calc_hstar_hwat_gofr_flag'
CALC_OH_GOFR = 'calc_ostar_hwat_gofr_flag'
CALC_TYPE_GOFR = 'calc_gofr_spec_type_flag'
# User inputs for g(r) calcs
GOFR_MAX = 'max_dist_for_gofr'
GOFR_DR = 'delta_r_for_gofr'
GOFR_BINS = 'bins_for_gofr'
GOFR_RAW_HIST = 'raw_histogram_for_gofr'

# with output from every frame types
CALC_OH_DIST = 'calc_hydroxyl_dist_flag'
# CALC_ALL_OH_DIST = 'calc_all_ostar_h_dist_flag'
CALC_HIJ_AMINO_FORM = 'calc_hij_amino_form_flag'
CALC_HIJ_WATER_FORM = 'calc_hij_water_form_flag'
COMBINE_OUTPUT = 'combine_output_flag'

# TODO: talk to Chris about listing many angles, dihedrals
CALC_COORD_NUM = 'calc_coord_number'
CALC_ANG_OCO = 'calc_carboxyl_o_c_o_ang'          # 18 17 19
CALC_ANG_COH = 'calc_carboxyl_c_o_h_ang'          # 17 ?? ??
CALC_DIH_CCCC = 'calc_carboxyl_ca_cb_cg_cd_dihed'  # 9 11 14 17
CALC_DIH_CCOH = 'calc_carboxyl_cg_cd_o_h_dihed'  # 14 17 ?? ??

# Added so I don't have to read all of a really big file
MAX_TIMESTEPS = 'max_timesteps_per_dumpfile'
PRINT_TIMESTEPS = 'print_output_every_x_timesteps'
PER_FRAME_OUTPUT = 'requires_output_for_every_frame'
PER_FRAME_OUTPUT_FLAGS = [CALC_OH_DIST, CALC_HIJ_AMINO_FORM, CALC_HIJ_WATER_FORM]
GOFR_OUTPUT = 'flag_for_gofr_output'
GOFR_OUTPUT_FLAGS = [CALC_HO_GOFR, CALC_OO_GOFR, CALC_HH_GOFR, CALC_OH_GOFR, CALC_TYPE_GOFR]

# Default max timesteps 1E12
DEF_MAX_TIMESTEPS = 1000000000000

# Defaults
DEF_CFG_FILE = 'lammps_proc_data.ini'
# Set notation
DEF_CFG_VALS = {DUMP_FILE_LIST: 'list.txt',
                DUMP_FILE: None,
                PROT_H_IGNORE: [],
                PROT_O_IDS: [],
                OUT_BASE_DIR: None,
                PER_FRAME_OUTPUT: False,
                CALC_OH_DIST: False,
                # CALC_ALL_OH_DIST: False,
                CALC_HIJ_AMINO_FORM: False,
                CALC_HIJ_WATER_FORM: False,
                GOFR_OUTPUT: False,
                CALC_HO_GOFR: False,
                CALC_OO_GOFR: False,
                CALC_HH_GOFR: False,
                CALC_OH_GOFR: False,
                CALC_TYPE_GOFR: False,
                GOFR_TYPE1: -1,
                GOFR_TYPE2: -1,
                GOFR_MAX: -1.1,
                GOFR_DR: -1.1,
                GOFR_BINS: [],
                GOFR_RAW_HIST: [],
                MAX_TIMESTEPS: DEF_MAX_TIMESTEPS,
                PRINT_TIMESTEPS: DEF_MAX_TIMESTEPS,
                COMBINE_OUTPUT: False,
                }
REQ_KEYS = {PROT_RES_MOL_ID: int,
            PROT_H_TYPE: int,
            WAT_O_TYPE: int,
            WAT_H_TYPE: int,
            H3O_O_TYPE: int,
            H3O_H_TYPE: int,
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


# for g(r) calcs
GOFR_R = 'gofr_r'
GOFR_HO = 'gofr_hsow'
GOFR_OO = 'gofr_osow'
GOFR_HH = 'gofr_hshw'
GOFR_OH = 'gofr_oshw'
GOFR_TYPE = 'gofr_type'
HO_BIN_COUNT = 'ho_bin_count'
OO_BIN_COUNT = 'oo_bin_count'
HH_BIN_COUNT = 'hh_bin_count'
OH_BIN_COUNT = 'oh_bin_count'
TYPE_BIN_COUNT = 'type_bin_count'
HO_STEPS_COUNTED = 'ho_steps_counted'
OO_STEPS_COUNTED = 'oo_steps_counted'
HH_STEPS_COUNTED = 'hh_steps_counted'
OH_STEPS_COUNTED = 'oh_steps_counted'
TYPE_STEPS_COUNTED = 'type_steps_counted'


# Values to output
TIMESTEP = 'timestep'
OH_MIN = 'oh_min'
OH_MAX = 'oh_max'
OH_DIFF = 'oh_diff'
R_OH = 'r_oh_dist'
R_OO = 'r_oo_dist'
Q_DOT = 'q_dotted'
HIJ_AMINO = 'hij_amino'
HIJ_ASP = 'hij_asp_params'
HIJ_GLU = 'hij_glu_params'
HIJ_WATER = 'hij_water_params'
HIJ_A1 = 'hij_water_termA1'
HIJ_A2 = 'hij_water_termA2'
HIJ_A3 = 'hij_water_termA3'
# OSTARH_MIN = 'o_star_h_min'
OH_FIELDNAMES = [OH_MIN, OH_MAX, OH_DIFF]
# OSTARH_FIELDNAMES = [OSTARH_MIN]
HIJ_AMINO_FIELDNAMES = [R_OH, HIJ_GLU, HIJ_ASP]
HIJ_WATER_FIELDNAMES = [R_OO, Q_DOT, HIJ_WATER, HIJ_A1, HIJ_A2, HIJ_A3]

# EVB Params
# asp/glu common parameters
d_0_OO = 2.400000
d_0_OH = 1.000000
rs_amino = 3.5
rc_amino = 4.0
D = 143.003
alpha = 1.8
r_0 = 0.975

# Asp params
B_asp = 0.579671
b_asp = 1.506881
bp_asp = 0.000108
C_asp = 0.579841
c_asp = 0.931593

Vii_asp = -150.505417

c1_asp = -25.099920
c2_asp = 2.799262
c3_asp = 1.299994

# Glu params

B_glu = 1.013770
b_glu = 1.418695
bp_glu = 1.084593
C_glu = 0.987714
c_glu = 1.146188

c1_glu = -25.013330
c2_glu = 3.018957
c3_glu = 1.280649

Vii_glu = -150.291915

# 3.2 water params from http://pubs.acs.org/doi/abs/10.1021/acs.jpcb.5b09466
gamma = 1.783170  # Angstrom^-2
P = 0.1559053
k_water = 5.0664471  # Angstrom^-2
D_OO_water = 2.8621690  # Angstrom
beta = 5.2394128  # Angstrom^-1
R_0_OO = 2.9425969
Pp = 7.6147672
a_water = 7.4062624
r_0_OO = 1.8
V_ij_water = -21.064268  # kcal/mol


# EVB Formulas

def u_morse(r):
    return D * (1 - np.exp(-alpha * (r - r_0))) ** 2


def hij_amino(r, c1, c2, c3):
    return c1 * np.exp(-c2 * (r - c3) ** 2)


def calc_q(r_o, r_op, r_h, box):
    """
    Calculates the 3-body term, keeping the pbc in mind
    @param r_o: x,y,z position of one oxygen donor/acceptor
    @param r_op: x,y,z position of the other oxygen donor/acceptor
    @param r_h: x,y,z position of the reactive H
    @param box: the dimensions of the periodic box (assumed 90 degree angles)
    @return: the dot-product of the vector q
    """
    # pbc_vector_avg
    q_vec = np.subtract(pbc_vector_avg(r_o, r_op, box), r_h)
    # would an average be faster?
    # q_vec = np.average(r_o, r_op) - r_h
    return np.dot(q_vec, q_vec)


def hij_water(r_oo, q_dot):
    term_a1 = np.exp(-gamma * q_dot)
    term_a2 = 1 + P * np.exp(-k_water * (r_oo - D_OO_water) ** 2)
    term_a3 = 0.5 * (1 - np.tanh(beta * (r_oo - R_0_OO))) + Pp * np.exp(-a_water * (r_oo - r_0_OO))
    return V_ij_water * 1.1 * term_a1 * term_a2 * term_a3, term_a1, term_a2, term_a3


def switch_func(rc, rs, r_array):
    """
    Switching function as in eq 9 of Wu Y, Chen H, Wang F, Paesani F, Voth GA. J Phys Chem B. 2008;112(2):467-482.
    doi:10.1021/jp076658h.
    @param rc: cut-off distance
    @param rs: switching distance
    @param r_array: an array of distance values
    @return: an array of smoothing values in range [0,1]
    """
    switches = np.zeros(len(r_array))
    for index, r in enumerate(r_array):
        if r <= rs:
            switches[index] = 1.00
        elif r < rc:
            switches[index] = 1 - (rc - rs) ** (-3) * (r - rs) ** 2 * (3 * rc - rs - 2 * r)
    return switches


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
    parser = argparse.ArgumentParser(description='Calculates properties of protonatable residues from lammps output. '
                                                 'Currently, this script expects only one protonatable residue.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run. The required keys are: "
                                               "{}".format(DEF_CFG_FILE, REQ_KEYS.keys()),
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
        warning("Invalid Data:", e)
        parser.print_help()
        return args, INVALID_DATA

    if len(args.config[PROT_O_IDS]) != 2:
        warning('Expected to find exactly two atom indices listed for the key {}. Check '
                'configuration file.'.format(PROT_O_IDS))
        return args, INVALID_DATA

    # TODO: is this where it should be?
    for flag in PER_FRAME_OUTPUT_FLAGS:
        if args.config[flag]:
            args.config[PER_FRAME_OUTPUT] = True
    for flag in GOFR_OUTPUT_FLAGS:
        if args.config[flag]:
            args.config[GOFR_OUTPUT] = True

    # TODO: write tests for specifying type calc
    if args.config[CALC_TYPE_GOFR]:
        if args.config[GOFR_TYPE1] < 1 or args.config[GOFR_TYPE2] < 1:
            warning('For g(r) calculation with specified types (requested by {} set to True), specify positive values '
                    'for configuration keys {} and {}. Check input data.'.format(GOFR_TYPE, GOFR_TYPE1, GOFR_TYPE2))
            return args, INVALID_DATA

    if args.config[GOFR_OUTPUT]:
        if args.config[GOFR_MAX] < 0.0 or args.config[GOFR_DR] < 0.0:
            warning('For requested g(r) calculation, a positive value for {} must be provided in the '
                    'configuration file. Check input data.'.format(GOFR_MAX))
            return args, INVALID_DATA

    if not args.config[GOFR_OUTPUT] and not args.config[PER_FRAME_OUTPUT]:
        warning('No calculations have been requested. Program exiting without action.\n '
                'Set at least one of the following option flags to be True: \n  '
                '{}'.format('  \n'.join(PER_FRAME_OUTPUT_FLAGS)))
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def calc_pair_dists(atom_a_list, atom_b_list, box):
    dist = np.zeros(len(atom_a_list) * len(atom_b_list))
    dist_index = 0
    for atom_a in atom_a_list:
        for atom_b in atom_b_list:
            dist[dist_index] = pbc_dist(np.asarray(atom_a[XYZ_COORDS]), np.asarray(atom_b[XYZ_COORDS]), box)
            dist_index += 1
    return dist


def find_closest_excess_proton(carboxyl_oxys, prot_h, hydronium, box, cfg):
    # initialize minimum distance to maximum distance possible in the periodic box (assume 90 degree corners)
    min_dist = np.full(len(carboxyl_oxys), np.linalg.norm(np.divide(box, 2)))
    closest_h = {}
    alt_dist = np.nan
    for index, oxy in enumerate(carboxyl_oxys):
        if prot_h is None:
            for atom in hydronium:
                if atom[ATOM_TYPE] == cfg[H3O_H_TYPE]:
                    dist = pbc_dist(np.asarray(atom[XYZ_COORDS]), np.asarray(oxy[XYZ_COORDS]), box)
                    if dist < min_dist[index]:
                        min_dist[index] = dist
                        closest_h[index] = atom
        else:
            min_dist[index] = pbc_dist(np.asarray(prot_h[XYZ_COORDS]), np.asarray(oxy[XYZ_COORDS]), box)
            closest_h[index] = prot_h
    index_min = np.argmin(min_dist)
    min_min = min_dist[index_min]
    o_star = carboxyl_oxys[index_min]
    excess_proton = closest_h[index_min]
    # The distance calculated again below because this will ensure that the 2nd return distance uses the same excess
    # proton
    for index, oxy in enumerate(carboxyl_oxys):
        if index != index_min:
            alt_dist = pbc_dist(np.asarray(excess_proton[XYZ_COORDS]), np.asarray(oxy[XYZ_COORDS]), box)
    alt_min = np.amin(alt_dist)
    return excess_proton, o_star, {OH_MIN: min_min,
                                   OH_MAX: alt_min,
                                   OH_DIFF: alt_min - min_min,
                                   }


def find_closest_o_to_ostar(water_oxys, o_star, hydronium, box, h30_atom_type):
    """
    Calculate the minimum distance between a water oxygen and the protonatable oxygen atom closest to the excess proton
    @param water_oxys:
    @param o_star: the protonatable oxygen atom closest to the excess proton
    @param hydronium: the list of atoms in the hydronium, if there is a hydronium
    @param box: the dimensions of the periodic box (assumed 90 degree angles)
    @param h30_atom_type: (int) lammps type for h30 oxygen atom
    @return: the water oxygen (or hydronium oxygen) closest to the o_star, and the distance between them
    """
    # initialize smallest distance to the maximum distance in a periodic box
    min_dist = np.linalg.norm(np.divide(box, 2))
    closest_o = None
    if not hydronium:
        # initialize minimum distance to maximum distance allowed in the PBC
        for wat_o in water_oxys:
            dist = pbc_dist(np.asarray(wat_o[XYZ_COORDS]), np.asarray(o_star[XYZ_COORDS]), box)
            if dist < min_dist:
                min_dist = dist
                closest_o = wat_o
    else:
        for atom in hydronium:
            if atom[ATOM_TYPE] == h30_atom_type:
                min_dist = pbc_dist(np.asarray(atom[XYZ_COORDS]), np.asarray(o_star[XYZ_COORDS]), box)
                closest_o = atom

    return closest_o, min_dist


def process_atom_data(cfg, dump_atom_data, box, timestep, gofr_data):
    carboxyl_oxys = []
    water_oxys = []
    # dictionary so can index by mol_num
    water_hs = []
    excess_proton = None
    hydronium = []
    type1 = []
    type2 = []
    calc_results = {}
    oh_dist_dict = {}
    for atom in dump_atom_data:
        if atom[MOL_NUM] == cfg[PROT_RES_MOL_ID]:
            if atom[ATOM_NUM] in cfg[PROT_O_IDS]:
                carboxyl_oxys.append(atom)
            elif (atom[ATOM_TYPE] == cfg[PROT_H_TYPE]) and (atom[ATOM_NUM] not in cfg[PROT_H_IGNORE]):
                excess_proton = atom
        elif atom[ATOM_TYPE] == cfg[WAT_O_TYPE]:
            water_oxys.append(atom)
        elif atom[ATOM_TYPE] == cfg[WAT_H_TYPE]:
            water_hs.append(atom)
        elif atom[ATOM_TYPE] == cfg[H3O_O_TYPE] or atom[ATOM_TYPE] == cfg[H3O_H_TYPE]:
            hydronium.append(atom)
        if cfg[CALC_TYPE_GOFR]:
            if atom[ATOM_TYPE] == cfg[GOFR_TYPE1]:
                type1.append(atom)
            if atom[ATOM_TYPE] == cfg[GOFR_TYPE2]:
                type2.append(atom)

    # Data checking
    if excess_proton is None:
        if len(hydronium) != 4:
            raise InvalidDataError("No excess proton found, so expected to find exactly 4 hydronium atoms.\n          "
                                   "However, found {} hydronium atoms at timestep {}. "
                                   "Check input data, including '{}' and '{}'.".format(len(hydronium), timestep,
                                                                                       H3O_O_TYPE, H3O_H_TYPE))
    else:
        if len(hydronium) != 0:
            raise InvalidDataError('Excess proton found, so expected to find exactly 0 hydronium atoms.\n          '
                                   'However, found {} hydronium atoms at timestep {}. '
                                   "Check input data, including '{}' and '{}'.".format(len(hydronium), timestep,
                                                                                       H3O_O_TYPE, H3O_H_TYPE))

    if len(carboxyl_oxys) != 2:
        raise InvalidDataError("Expected to find exactly 2 atom indices {} in resid {} (to be treated as "
                               "carboxylic oxygen atoms). \n          Found {} such indices at timestep {}. "
                               "Check input data, including '{}' and '{}'."
                               "".format(cfg[PROT_O_IDS], cfg[PROT_RES_MOL_ID],
                                         len(carboxyl_oxys), timestep, PROT_RES_MOL_ID, PROT_O_IDS))
    if len(water_oxys) == 0:
        raise InvalidDataError("The configuration file listed '{}' = {}, however no such atoms were found. "
                               "Check input data.".format(WAT_O_TYPE, cfg[WAT_O_TYPE]))
    if len(water_hs) == 0:
        raise InvalidDataError("The configuration file listed '{}' = {}, however no such atoms were found. "
                               "Check input data.".format(WAT_H_TYPE, cfg[WAT_H_TYPE]))

    # Now start looking for data to report
    if cfg[CALC_OH_DIST] or cfg[CALC_HIJ_AMINO_FORM] or cfg[CALC_HIJ_WATER_FORM]:
        closest_excess_h, o_star, oh_dist_dict = find_closest_excess_proton(carboxyl_oxys, excess_proton,
                                                                            hydronium, box, cfg)
        if cfg[CALC_HIJ_WATER_FORM]:
            closest_o_to_ostar, o_ostar_dist = find_closest_o_to_ostar(water_oxys, o_star, hydronium, box,
                                                                       cfg[H3O_O_TYPE])
            q_dot = calc_q(closest_o_to_ostar[XYZ_COORDS], o_star[XYZ_COORDS], closest_excess_h[XYZ_COORDS], box)
            hij_wat, term_a1, term_a2, term_a3 = hij_water(o_ostar_dist, q_dot)
            calc_results.update({R_OO: o_ostar_dist, Q_DOT: q_dot, HIJ_WATER: hij_wat,
                                 HIJ_A1: term_a1, HIJ_A2: term_a2, HIJ_A3: term_a3, })
    if cfg[CALC_OH_DIST]:
        if excess_proton is None:
            calc_results.update({OH_MIN: 'nan', OH_MAX: 'nan', OH_DIFF: 'nan'})
        else:
            calc_results.update(oh_dist_dict)
    if cfg[CALC_HIJ_AMINO_FORM]:
        r_oh = oh_dist_dict[OH_MIN]
        hij_glu = hij_amino(r_oh, c1_glu, c2_glu, c3_glu)
        hij_asp = hij_amino(r_oh, c1_asp, c2_asp, c3_asp)
        calc_results.update({R_OH: oh_dist_dict[OH_MIN], HIJ_GLU: hij_glu, HIJ_ASP: hij_asp})

    # For calcs requiring H* (proton on protonated residue) skip timesteps when there is no H* (residue deprotonated)
    if cfg[GOFR_OUTPUT]:
        if excess_proton is not None:
            if cfg[CALC_HO_GOFR]:
                num_dens = len(water_oxys) / np.prod(box)
                ho_dists = (calc_pair_dists([excess_proton], water_oxys, box))
                step_his = np.histogram(ho_dists, gofr_data[GOFR_BINS])
                gofr_data[HO_BIN_COUNT] = np.add(gofr_data[HO_BIN_COUNT], np.divide(step_his[0], num_dens))
                gofr_data[HO_STEPS_COUNTED] += 1
            if cfg[CALC_HH_GOFR]:
                num_dens = len(water_hs) / np.prod(box)
                hh_dists = (calc_pair_dists([excess_proton], water_hs, box))
                step_his = np.histogram(hh_dists, gofr_data[GOFR_BINS])
                gofr_data[HH_BIN_COUNT] = np.add(gofr_data[HH_BIN_COUNT], np.divide(step_his[0], num_dens))
                gofr_data[HH_STEPS_COUNTED] += 1
        if cfg[CALC_OO_GOFR]:
            num_dens = (len(carboxyl_oxys) * len(water_oxys)) / np.prod(box)
            oo_dists = (calc_pair_dists(carboxyl_oxys, water_oxys, box))
            step_his = np.histogram(oo_dists, gofr_data[GOFR_BINS])
            gofr_data[OO_BIN_COUNT] = np.add(gofr_data[OO_BIN_COUNT], np.divide(step_his[0], num_dens))
            gofr_data[OO_STEPS_COUNTED] += 1
        if cfg[CALC_OH_GOFR]:
            num_dens = (len(carboxyl_oxys) * len(water_hs)) / np.prod(box)
            oh_dists = (calc_pair_dists(carboxyl_oxys, water_hs, box))
            step_his = np.histogram(oh_dists, gofr_data[GOFR_BINS])
            gofr_data[OH_BIN_COUNT] = np.add(gofr_data[OH_BIN_COUNT], np.divide(step_his[0], num_dens))
            gofr_data[OH_STEPS_COUNTED] += 1
        if cfg[CALC_TYPE_GOFR]:
            if len(type1) > 0 and len(type2) > 0:
                num_dens = (len(type1) * len(type2)) / np.prod(box)
                type_dists = (calc_pair_dists(type1, type2, box))
                step_his = np.histogram(type_dists, gofr_data[GOFR_BINS])
                gofr_data[TYPE_BIN_COUNT] = np.add(gofr_data[TYPE_BIN_COUNT], np.divide(step_his[0], num_dens))
                gofr_data[TYPE_STEPS_COUNTED] += 1

    return calc_results


def read_dump_file(dump_file, cfg, data_to_print, gofr_data, out_fieldnames, write_mode):
    with open(dump_file) as d:
        # spaces here allow file name to line up with the "completed reading" print line
        print("{:>17}: {}".format('Reading', dump_file))
        section = None
        box = np.zeros((3,))
        box_counter = 1
        atom_counter = 1
        timesteps_read = 0
        num_atoms = 0
        timestep = None
        for line in d:
            line = line.strip()
            if section is None:
                section = find_dump_section_state(line)
                if section is None and len(line) > 0:
                    raise InvalidDataError('Unexpected line in file {}: {}'.format(dump_file, line))
            elif section == SEC_TIMESTEP:
                # Reset variables
                section = None
                dump_atom_data = []
                try:
                    timestep = int(line)
                except ValueError as e:
                    raise InvalidDataError("In attempting to read an integer timestep, encountered error: {}".format(e))
                timesteps_read += 1
                if timesteps_read > cfg[MAX_TIMESTEPS]:
                    print("Reached the maximum timesteps per dumpfile ({}). "
                          "To increase this number, set a larger value for {}. "
                          "Continuing program.".format(cfg[MAX_TIMESTEPS], MAX_TIMESTEPS))
                    break
                if timesteps_read % cfg[PRINT_TIMESTEPS] == 0:
                    if cfg[PER_FRAME_OUTPUT]:
                        print_per_frame(dump_file, cfg, data_to_print, out_fieldnames, write_mode)
                        data_to_print = []
                        write_mode = 'a'
                    if cfg[GOFR_OUTPUT]:
                        print_gofr(cfg, gofr_data)
                result = {TIMESTEP: timestep}
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
                # If there is an incomplete line in a dump file, move on to the next file
                if len(split_line) < 7:
                    break
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
                               XYZ_COORDS: [x, y, z], }
                dump_atom_data.append(atom_struct)
                if atom_counter == num_atoms:
                    result.update(process_atom_data(cfg, dump_atom_data, box, timestep, gofr_data))
                    data_to_print.append(result)
                    atom_counter = 0
                    section = None
                atom_counter += 1
    if atom_counter == 1:
        print("Completed reading: {}".format(dump_file))
    else:
        warning("FYI: dump file {} step {} did not have the full list of atom numbers. "
                "Continuing to next dump file.".format(dump_file, timestep))


def setup_per_frame_output(cfg):
    out_fieldnames = [TIMESTEP]
    if cfg[CALC_OH_DIST]:
        out_fieldnames.extend(OH_FIELDNAMES)
    if cfg[CALC_HIJ_AMINO_FORM]:
        out_fieldnames.extend(HIJ_AMINO_FIELDNAMES)
    if cfg[CALC_HIJ_WATER_FORM]:
        out_fieldnames.extend(HIJ_WATER_FIELDNAMES)
    return out_fieldnames


def print_gofr(cfg, gofr_data):
    g_dr = cfg[GOFR_DR]
    dr_array = gofr_data[GOFR_BINS][1:] - g_dr / 2
    gofr_out_fieldnames = [GOFR_R]
    gofr_output = dr_array
    if cfg[CALC_HO_GOFR]:
        normal_fac = np.square(dr_array) * gofr_data[HO_STEPS_COUNTED] * 4 * np.pi * g_dr
        gofr_ho = np.divide(gofr_data[HO_BIN_COUNT], normal_fac)
        gofr_out_fieldnames.append(GOFR_HO)
        gofr_output = np.column_stack((gofr_output, gofr_ho))
    if cfg[CALC_OO_GOFR]:
        normal_fac = np.square(dr_array) * gofr_data[OO_STEPS_COUNTED] * 4 * np.pi * g_dr
        gofr_oo = np.divide(gofr_data[OO_BIN_COUNT], normal_fac)
        gofr_out_fieldnames.append(GOFR_OO)
        gofr_output = np.column_stack((gofr_output, gofr_oo))
    if cfg[CALC_HH_GOFR]:
        normal_fac = np.square(dr_array) * gofr_data[HH_STEPS_COUNTED] * 4 * np.pi * g_dr
        gofr_hh = np.divide(gofr_data[HH_BIN_COUNT], normal_fac)
        gofr_out_fieldnames.append(GOFR_HH)
        gofr_output = np.column_stack((gofr_output, gofr_hh))
    if cfg[CALC_OH_GOFR]:
        normal_fac = np.square(dr_array) * gofr_data[OH_STEPS_COUNTED] * 4 * np.pi * g_dr
        gofr_oh = np.divide(gofr_data[OH_BIN_COUNT], normal_fac)
        gofr_out_fieldnames.append(GOFR_OH)
        gofr_output = np.column_stack((gofr_output, gofr_oh))
    if cfg[CALC_TYPE_GOFR]:
        if gofr_data[TYPE_STEPS_COUNTED] > 0:
            normal_fac = np.square(dr_array) * gofr_data[TYPE_STEPS_COUNTED] * 4 * np.pi * g_dr
            gofr_type = np.divide(gofr_data[TYPE_BIN_COUNT], normal_fac)
            gofr_out_fieldnames.append(GOFR_TYPE)
            gofr_output = np.column_stack((gofr_output, gofr_type))
        else:
            warning("Did not find any timesteps with the pairs in {}. "
                    "This output will not be printed.".format(CALC_TYPE_GOFR))

    f_out = create_out_fname(cfg[DUMP_FILE_LIST], suffix='_gofrs', ext='.csv', base_dir=cfg[OUT_BASE_DIR])
    # list_to_file([gofr_out_fieldnames] + gofr_output.tolist(), f_out, delimiter=',')
    list_to_csv([gofr_out_fieldnames] + gofr_output.tolist(), f_out)


def print_per_frame(dump_file, cfg, data_to_print, out_fieldnames, write_mode):
    f_out = create_out_fname(dump_file, suffix='_proc_data', ext='.csv', base_dir=cfg[OUT_BASE_DIR])
    write_csv(data_to_print, f_out, out_fieldnames, extrasaction="ignore", mode=write_mode)


def ini_gofr_data(gofr_data, bin_count, bins, step_count):
    gofr_data[bin_count] = np.zeros(len(gofr_data[bins]) - 1)
    gofr_data[step_count] = 0


def process_dump_files(cfg):
    """
    @param cfg: configuration data read from ini file
    """
    gofr_data = {}
    out_fieldnames = None

    # If RDFs are to be calculated, initialize empty data structures
    if cfg[GOFR_OUTPUT]:
        g_dr = cfg[GOFR_DR]
        g_max = cfg[GOFR_MAX]
        gofr_data[GOFR_BINS] = np.arange(0.0, g_max + g_dr, g_dr)
        if len(gofr_data[GOFR_BINS]) < 2:
            raise InvalidDataError("Insufficient number of bins to calculate RDFs. Check input: "
                                   "{}: {}, {}: {},".format(GOFR_DR, cfg[GOFR_DR], GOFR_MAX, cfg[GOFR_MAX]))
        if cfg[CALC_HO_GOFR]:
            ini_gofr_data(gofr_data, HO_BIN_COUNT, GOFR_BINS, HO_STEPS_COUNTED)
        if cfg[CALC_OO_GOFR]:
            ini_gofr_data(gofr_data, OO_BIN_COUNT, GOFR_BINS, OO_STEPS_COUNTED)
        if cfg[CALC_HH_GOFR]:
            ini_gofr_data(gofr_data, HH_BIN_COUNT, GOFR_BINS, HH_STEPS_COUNTED)
        if cfg[CALC_OH_GOFR]:
            ini_gofr_data(gofr_data, OH_BIN_COUNT, GOFR_BINS, OH_STEPS_COUNTED)
        if cfg[CALC_TYPE_GOFR]:
            ini_gofr_data(gofr_data, TYPE_BIN_COUNT, GOFR_BINS, TYPE_STEPS_COUNTED)

    if cfg[PER_FRAME_OUTPUT]:
        out_fieldnames = setup_per_frame_output(cfg)

    dump_file_list = []

    if os.path.isfile(cfg[DUMP_FILE_LIST]):
        with open(cfg[DUMP_FILE_LIST]) as f:
            for dump_file in f:
                dump_file = dump_file.strip()
                # skip any excess blank lines
                if len(dump_file) > 0:
                    dump_file_list.append(dump_file)
    if cfg[DUMP_FILE] is not None:
        dump_file_list.append(cfg[DUMP_FILE])

    if len(dump_file_list) == 0:
        raise InvalidDataError("Found no dump files to process. Use the configuration ('ini') file to specify the name "
                               "of a single dump file with the keyword '{}' or a file listing dump files with the "
                               "keyword '{}'.".format(DUMP_FILE, DUMP_FILE_LIST))

    per_frame_write_mode = 'w'
    base_out_file_name = cfg[DUMP_FILE_LIST]
    for dump_file in dump_file_list:
        data_to_print = []
        # output file base name to change at each iteration if not combining output
        if cfg[COMBINE_OUTPUT] is False:
            base_out_file_name = dump_file
        read_dump_file(dump_file, cfg, data_to_print, gofr_data, out_fieldnames, per_frame_write_mode)
        if cfg[PER_FRAME_OUTPUT]:
            print_per_frame(base_out_file_name, cfg, data_to_print, out_fieldnames, per_frame_write_mode)
        # if combining files, after first loop, always append to file
        if cfg[COMBINE_OUTPUT]:
            per_frame_write_mode = 'a'

    if cfg[GOFR_OUTPUT]:
        print_gofr(cfg, gofr_data)


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
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
