#!/usr/bin/env python
"""
Get selected info from the data file
"""

from __future__ import print_function
import ConfigParser
import logging
import re
import sys
import argparse

from md_utils.md_common import InvalidDataError, warning, process_cfg

__author__ = 'hmayes'


# Logging
logger = logging.getLogger('psf_get_info')
logging.basicConfig(filename='psf_get_info.log', filemode='w', level=logging.DEBUG)
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
RESID_LIST = 'resid_list'

# data file info


# Defaults
DEF_CFG_FILE = 'psf_get_info.ini'
# Set notation
DEF_CFG_VALS = {
}
REQ_KEYS = {PSF_FILE: str, RESID_LIST: [],
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


def to_int_list(raw_val):
    return_vals = []
    for val in raw_val.split(','):
        return_vals.append(int(val.strip()))
    return return_vals


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
    parser = argparse.ArgumentParser(description='Grabs selected info rom the psf file.'
                                                 'The required input file provides the location of the '
                                                 'file and the data requested.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini "
                                               "format. See the example file /test/test_data/data2data/data_get_info. "
                                               "The default file name is data_get_info.ini, located in the "
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


def print_qm_kind(int_list, element_name):
    print('    &QM_KIND {}'.format(element_name))
    print('        MM_INDEX {}'.format(' '.join(map(str,int_list))))
    print('    &END QM_KIND')
    return


def print_qm_links(resid, dict):
    print('    &LINK \n       MM_INDEX  {}\n       QM_INDEX  {}\n       LINK_TYPE  IMOMM\n       ALPHA_IMOMM  1.5\n'
          '    &END LINK '.format(dict['CA'],dict['CB']))
    return


def process_data_tpl(cfg):

    psf_loc = cfg[PSF_FILE]
    psf_data = {HEAD_CONTENT: [], ATOMS_CONTENT: [], TAIL_CONTENT: []}

    prot_seg = 'P1'
    keep_resids = [763, 767, 794, 799, 908, 944]
    resid_dict_dicts = {}
    for resid in keep_resids:
        resid_dict_dicts[resid] = {}

    backbone_types = ['N', 'HN', 'CA', 'HA', 'C', 'O', ]
    # The "res_types" are the kinds I know to look for. I use to to check that I look for all the appropriate types.
    res_types = ['HSD', 'TYR', 'SER', 'TRP', 'MET', 'GLU', 'VAL', 'THR']
    tyr_types = ['CB', 'HB1', 'HB2', 'CG', 'CD1', 'HD1', 'CE1', 'HE1', 'CZ', 'OH', 'HH', 'CD2', 'HD2', 'CE2', 'HE2', ]
    ser_types = ['CB', 'HB1', 'HB2', 'OG', 'HG1']
    trp_types = ['HH2', 'HE1', 'HD1', 'HE3', 'CZ2', 'CB', 'HZ2', 'CG', 'CH2', 'CE2', 'CE3', 'CD1', 'CD2', 'CZ3', 'NE1',
                 'HB1', 'HZ3', 'HB2']
    hsd_types = ['CD2', 'HD2', 'HE1', 'HD1', 'CB', 'CG', 'NE2', 'CE1', 'ND1', 'HB1', 'HB2']
    met_types = ['HE1', 'HE2', 'HE3', 'CB', 'CG', 'CE', 'HG1', 'SD', 'HG2', 'HB1', 'HB2']
    glu_types = ['CB', 'OE1', 'CG', 'HG1', 'CD', 'OE2', 'HG2', 'HB1', 'HB2']
    val_types = ['HG22', 'HG11', 'CB', 'HG21', 'CG1', 'HG12', 'HG13', 'HB', 'HG23', 'CG2']
    thr_types = ['HG22', 'CB', 'OG1', 'HG1', 'HG21', 'HB', 'HG23', 'CG2']
    keep_types = set(tyr_types + ser_types + trp_types + hsd_types + met_types +  glu_types + val_types + thr_types)
    h_types = ['HH2', 'HE1', 'HE2', 'HE3', 'HG21', 'HB2', 'HG2', 'HG12', 'HG1', 'HG11', 'HH', 'HG13', 'HZ3', 'HZ2',
               'HB', 'HD1', 'HG22', 'HB1', 'HG23', 'HD2']
    o_types = ['OG', 'OE2', 'OE1', 'OG1', 'OH']
    c_types = ['CE1', 'CZ2', 'CZ3', 'CG', 'CE', 'CD', 'CZ', 'CH2', 'CE3', 'CD1', 'CD2', 'CB', 'CG1', 'CG2', 'CE2']
    n_types = ['ND1', 'NE2', 'NE1']
    s_types = ['SD']
    element_types = set(h_types + o_types + c_types + n_types + s_types)

    h_ids = []
    o_ids = []
    c_ids = []
    n_ids = []
    s_ids = []

    section = SEC_HEAD
    to_print = set()
    num_atoms_pat = re.compile(r"(\d+).*NATOM$")

    for item in keep_types:
        if item not in element_types:
            raise InvalidDataError('The atom lists may miss some ids because the code will not look for type '
                                   '{}.'.format(item))

    # t_pat = re.compile(r"^S.*")
    # for item in keep_types:
    #     t_match = t_pat.match(item)
    #     if t_match:
    #         to_print.add(item)

    vmd_atom_ids = []

    with open(psf_loc) as f:
        for line in f.readlines():
            line = line.strip()
            # head_content to contain Everything before 'Atoms' section
            # also capture the number of atoms
            if section == SEC_HEAD:
                psf_data[HEAD_CONTENT].append(line)

                atoms_match = num_atoms_pat.match(line)
                if atoms_match:
                    # regex is 1-based
                    psf_data[NUM_ATOMS] = int(atoms_match.group(1))
                    section = SEC_ATOMS

            elif section == SEC_ATOMS:
                if len(line) == 0:
                    continue
                split_line = line.split()
                atom_num = int(split_line[0])
                segid = split_line[1]
                resid = int(split_line[2])
                resname = split_line[3]
                atom_type = split_line[4]
                charmm_type =  split_line[5]
                charge = float(split_line[6])
                atom_wt = float(split_line[7])

                atom_struct = [atom_num, segid, resid, resname, atom_type, charmm_type, charge, atom_wt]
                psf_data[ATOMS_CONTENT].append(atom_struct)
                if segid == prot_seg:
                    if resid in keep_resids:
                        if resname not in res_types:
                            raise InvalidDataError('Note that the code does not know to look for atom types of the '
                                                   'residue {}. Update program and rerun.'.format(resname))
                            ### This code is useful to find types for a residue type.
                            ## TODO: update for all residue types
                            # if resname == 'THR':
                            #     print(atom_struct)
                            #     if atom_type not in backbone_types:
                            #         to_print.add(atom_type)
                        if atom_type == 'CA' or atom_type == 'CB':
                            resid_dict_dicts[resid][atom_type] = atom_num
                        if atom_type in keep_types:
                            vmd_atom_ids.append(atom_num -1)
                            if atom_type in h_types:
                                h_ids.append(atom_num)
                            elif atom_type in o_types:
                                o_ids.append(atom_num)
                            elif atom_type in c_types:
                                c_ids.append(atom_num)
                            elif atom_type in n_types:
                                n_ids.append(atom_num)
                            elif atom_type in s_types:
                                s_ids.append(atom_num)
                            else:
                                raise InvalidDataError('Did not add {} atoms to QM lists.'.format(atom_type))

                if len(psf_data[ATOMS_CONTENT]) == psf_data[NUM_ATOMS]:
                    section = SEC_TAIL
            # tail_content to contain everything after the 'Atoms' section
            elif section == SEC_TAIL:
                psf_data[TAIL_CONTENT].append(line)

    # if logger.isEnabledFor(logging.DEBUG):
    #     list_to_file(psf_data[HEAD_CONTENT] + psf_data[ATOMS_CONTENT] + psf_data[TAIL_CONTENT], 'reproduced.data')

    print_qm_kind(h_ids,'H')
    print_qm_kind(o_ids,'O')
    print_qm_kind(c_ids,'C')
    print_qm_kind(n_ids,'N')
    print_qm_kind(s_ids,'S')

    print('index {}'.format(' '.join(map(str,vmd_atom_ids))))

    for key in keep_resids:
        print_qm_links(key,resid_dict_dicts[key])

    print(to_print)
    return psf_data

def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    # Read template and data files
    cfg = args.config

    try:
        psf_data_content = process_data_tpl(cfg)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data template:", e)
        return INVALID_DATA

    # print(psf_data_content[ATOMS_CONTENT])

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
