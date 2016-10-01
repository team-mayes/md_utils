#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Finds the distances between each pair of atoms listed in the pair file for each time step in the given
LAMMPS dump file.
"""
import argparse
import csv
import logging
import os
import sys
from collections import OrderedDict

import itertools
from md_utils.lammps import find_atom_data
from md_utils.md_common import xyz_distance, InvalidDataError, unique_list, create_out_fname, GOOD_RET, INPUT_ERROR, \
    warning, IO_ERROR, file_rows_to_list

logger = logging.getLogger(__name__)

# Constants #

FILENAME = 'filename'
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
        pair_dist = OrderedDict({FILENAME: os.path.basename(rst)})
        for pair in atom_pairs:
            try:
                row1 = atoms[pair[0]]
                row2 = atoms[pair[1]]
                pair_dist[pair] = xyz_distance(row1[-3:], row2[-3:])
            except KeyError as e:
                warning(MISSING_TSTEP_ATOM_MSG.format(rst, tstep, e))
                return
        results[tstep] = pair_dist
    return results


def write_results(out_fname, dist_data, atom_pairs, write_mode='w'):
    with open(out_fname, write_mode) as o_file:
        o_writer = csv.writer(o_file, quoting=csv.QUOTE_NONNUMERIC)
        # add header only if write mode (if appending, do not add header)
        if write_mode == 'w':
            o_writer.writerow([FILENAME, "timestep"] +
                              ["_".join(map(str, t_pair)) for t_pair in atom_pairs])
        for tstep, pair_dists in dist_data.items():
            f_name = pair_dists[FILENAME]
            dist_row = [f_name, tstep]
            pair = None
            try:
                for pair in atom_pairs:
                    dist_row.append(round(pair_dists[pair], 6))
                o_writer.writerow(dist_row)
            except KeyError as e:
                raise InvalidDataError(MISSING_TSTEP_ATOM_MSG.format("_".join(map(str, pair)), tstep, e))
    if write_mode == 'w':
        print("Wrote file: {}".format(out_fname))
    elif write_mode == 'a':
        print("  Appended: {}".format(out_fname))


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
                    logger.warn("Skipping pair {} from file {}".format(pair, p_file))
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
    parser.add_argument("-f", "--file", help="The dump file to process", default=None)
    parser.add_argument("-l", "--list_file", help="The file with a list of dump files to process", default=None)

    args = None
    try:
        args = parser.parse_args(argv)
        if not args.pair_files:
            args.pair_files.append(DEF_PAIRS_FILE)
            if not os.path.isfile(DEF_PAIRS_FILE):
                raise InvalidDataError("No pair file specified and did not find the default "
                                       "pair file: {}".format(DEF_PAIRS_FILE))
        if (args.file is None) and (args.list_file is None):
            raise InvalidDataError("Specify either a file or list of files to process.")
    except (KeyError, InvalidDataError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


def main(argv=None):
    """
    Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    try:
        if args.list_file is None:
            file_list = []
            base_file_name = args.file
        else:
            file_list = file_rows_to_list(args.list_file)
            base_file_name = args.list_file
        if args.file is not None:
            file_list.append(args.file)

        dists = OrderedDict()
        pairs = parse_pairs(args.pair_files)
        write_mode = 'w'
        for l_file in file_list:
            dists.update(atom_distances(l_file, pairs))
            write_results(create_out_fname(base_file_name, prefix='pairs_', ext='.csv'),
                          dists, pairs, write_mode=write_mode)
            write_mode = 'a'
    except IOError as e:
        warning("Problems reading file: {}".format(e))
        return IO_ERROR
    except InvalidDataError as e:
        warning("Invalid Data Error: {}".format(e))
        return IO_ERROR

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
