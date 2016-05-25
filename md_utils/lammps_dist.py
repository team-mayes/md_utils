#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Finds the distances between each pair of atoms listed in the pair file for each time step in the given
LAMMPS dump file.
"""
import argparse
import csv
import logging
import sys
from collections import OrderedDict

import itertools
from md_utils.lammps import find_atom_data
from md_utils.md_common import xyz_distance, InvalidDataError, unique_list, create_out_fname

logger = logging.getLogger(__name__)

# Constants #

MISSING_TSTEP_ATOM_MSG = "Couldn't find an atom in file {} for timestep {}: {}"
DEF_PAIRS_FILE = 'atom_pairs.txt'


# Logic #

def atom_distances(rst, atom_pairs):
    """Finds the distance between the each of the atom pairs in the
    given LAMMPS dump file.

    :param rst: A file in the LAMMPS dump format.
    :param atom_pairs: Zero or more pairs of atom IDs to compare.
    :returns: Nested dicts keyed by time step, then pair, with the distance as the value.
    """
    results = OrderedDict()
    flat_ids = set(itertools.chain.from_iterable(atom_pairs))
    tstep_atoms = find_atom_data(rst, flat_ids)

    for tstep, atoms in tstep_atoms.items():
        pair_dist = OrderedDict()
        for pair in atom_pairs:
            try:
                row1 = atoms[pair[0]]
                row2 = atoms[pair[1]]
                pair_dist[pair] = xyz_distance(row1[-3:], row2[-3:])
            except KeyError as e:
                raise InvalidDataError(MISSING_TSTEP_ATOM_MSG.format(
                    rst, tstep, e))
        results[tstep] = pair_dist
    return results


def write_results(out_fname, dist_data, atom_pairs):
    with open(out_fname, 'w') as o_file:
        o_writer = csv.writer(o_file)
        o_writer.writerow(["timestep"] +
                          ["_".join(map(str, t_pair)) for t_pair in atom_pairs])
        for tstep, pair_dists in dist_data.items():
            t_str = str(tstep)
            dist_row = [t_str]
            pair = None
            try:
                for pair in atom_pairs:
                    dist_row.append("{:.6f}".format(pair_dists[pair]))
                o_writer.writerow(dist_row)
            except KeyError as e:
                raise InvalidDataError(MISSING_TSTEP_ATOM_MSG.format(
                    "_".join(map(str, pair)), tstep, e))


def parse_pairs(pair_files):
    """Creates a list of unique two-element tuples representing the pairs described in the given pair files.

    :param pair_files: The files to process.
    :return: A list of unique pairs from the given files.
    """
    pairs = []
    for p_file in pair_files:
        with open(p_file) as o_file:
            for p_line in o_file:
                pair = p_line.strip().split(",")
                if len(pair) == 2:
                    pairs.append(tuple(map(int, pair)))
                else:
                    logger.warn("Skipping pair %s from file %s", pair, p_file)
    return unique_list(pairs)

# CLI Processing #


def parse_cmdline(argv=None):
    """
    Returns the parsed argument list and return code.
    :param argv: A list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Finds the distances between each pair '
                                                 'of atoms listed in the pair file for '
                                                 'each time step in the given LAMMPS dump '
                                                 'file.')
    parser.add_argument("-p", "--pair_files", action="append", default=[],
                        help="One or more files containing atom pairs (default {0})".format(
                            DEF_PAIRS_FILE))
    parser.add_argument("file", help="The dump file to process")
    args = parser.parse_args(argv)

    if not args.pair_files:
        args.pair_files.append(DEF_PAIRS_FILE)

    return args, 0


def main(argv=None):
    """
    Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != 0:
        return ret

    pairs = parse_pairs(args.pair_files)
    dists = atom_distances(args.file, pairs)
    write_results(create_out_fname(args.file, prefix='pairs_', ext='.csv'),
                  dists, pairs)

    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
