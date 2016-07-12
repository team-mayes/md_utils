# !/usr/bin/env python
# coding=utf-8

"""
Sorts the data in given XYZ input file into bins of the given interval, producing a VMD-formatted
file containing the average XYZ coordinate for each bin that contains two or more samples.  A
separate CSV-formatted log file is also produced, which provides the bin value, the number of
samples, and the average and standard deviation for X, Y, and Z.
"""
import argparse
from collections import defaultdict
import csv
import logging
import sys
import datetime
import os

import numpy as np

from md_utils.md_common import move_existing_file


__author__ = 'cmayes'

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('path_bin')
logger.setLevel(logging.INFO)

# Constants #

COORDS = ['x', 'y', 'z']
FLOAT_FMT = "{:.4f}"

# Logic #


def process_infile(infile, coord):
    """
    Parses the contents of the given file location, producing three return values:

    1. A list of lists containing the three-element float values of every valid line
    2. The maximum value of the given coordinate
    3. The minimum value of the given coordinate

    :param infile: The file location to process
    :param coord: The coordinate (x, y, z) to sample for max and min
    :return: The list, the max val, and the min val.
    """
    coord_pos = COORDS.index(coord)
    max_coord = None
    min_coord = None
    line_idx = defaultdict(list)
    with open(infile) as xyzfile:
        for xyzline in xyzfile:
            xyz = xyzline.split()
            if len(xyz) != 3:
                logger.warning("Skipping '%d'-element input line '%s'",
                            len(xyz), xyzline)
                continue

            try:
                # Explicitly convert to list as Python 3 returns an iterable
                float_xyz = list(map(float, xyz))
            except ValueError as e:
                logger.warning("Skipping non-float input line '%s'",
                            xyzline)
                continue

            line_coord_val = float_xyz[coord_pos]

            if max_coord is None or line_coord_val > max_coord:
                max_coord = line_coord_val

            if min_coord is None or line_coord_val < min_coord:
                min_coord = line_coord_val

            line_idx[line_coord_val].append(float_xyz)

    return line_idx, min_coord, max_coord


def bin_data(xyz_idx, min_val, max_val, step):
    """
    Creates bins based on the interval between the min and max val using the given step size.
    The XYZ coordinates in `xyz_idx` are indexed to their proper bin based on which bin matches
    the index key.  The function returns a list of bins and a dict mapping XYZ values to the
    bin that they match.

    :param xyz_idx: A dict mapping lists of XYZ values to the coordinate selected for binning.
    :param min_val: The minimum value for the coordinate selected for binning.
    :param max_val: The maximum value for the coordinate selected for binning.
    :param step: The size of the step to take for the bin range between the min and max values.
    :return: A list of the bin values and a dict of lists of the coordinates mapped to their assigned bins.
    """
    bins = np.arange(min_val + step, max_val + step, step)
    # Explicitly convert keys to list as Python 3 returns an iterable
    key_bin_idx = np.digitize(list(xyz_idx.keys()), bins)
    bin_idx = defaultdict(list)
    for idx, xyz_key in enumerate(xyz_idx.keys()):
        bin_idx_loc = key_bin_idx[idx]
        bin_idx[bins[bin_idx_loc]].extend(xyz_idx[xyz_key])

    short_bins = []
    for i, bin_num in enumerate(bins):
        bin_coords = bin_idx[bin_num]
        if len(bin_coords) < 2:
            logger.debug("Removing %d-point bin '%.4f'",
                         len(bin_coords), bin_num)
            short_bins.append(i)
            del bin_idx[bin_num]
    bins = np.delete(bins, short_bins)
    return bins, bin_idx


def write_results(bins, bin_data, src_file):
    base_fname = os.path.splitext(src_file)[0]
    xyz_file = base_fname + '.xyz'
    move_existing_file(xyz_file)
    log_file = base_fname + '.log'
    move_existing_file(log_file)
    with open(xyz_file, 'w') as xyz:
        xyz.write(str(len(bin_data)) + '\n')
        xyz.write("{} {}\n".format(src_file, datetime.datetime.today()))
        with open(log_file, 'w') as bin_log:
            csv_log = csv.writer(bin_log)
            csv_log.writerow(["bin", "count","ax","dx","ay","dy","az","dz"])
            for cur_bin in bins:
                if cur_bin in bin_data:
                    bin_coords = bin_data[cur_bin]
                    bin_mean = list(map(np.mean, zip(*bin_coords)))
                    bin_stdev = list(map(np.std, zip(*bin_coords)))
                    xyz.write("B   {: .4f}   {: .4f}   {: .4f}\n".format(
                        *bin_mean))
                    merged_xyz = [item for sublist in zip(bin_mean, bin_stdev) for item in sublist]
                    csv_log.writerow([FLOAT_FMT.format(cur_bin), len(bin_coords)] +
                                     [FLOAT_FMT.format(coord) for coord in merged_xyz])

# CLI Processing #


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    :param argv: is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Sorts the data in given XYZ input file '
                                                 'into bins of the given interval, producing '
                                                 'a VMD-formatted file containing the average '
                                                 'XYZ coordinate, plus a detailed log file.')
    parser.add_argument("-s", "--bin_size", help="The size interval for each bin in Angstroms",
                        default=0.1, type=float)
    parser.add_argument("-c", "--bin_coordinate", help='The xyz coordinate to use for bin sorting',
                        default='z', choices=COORDS)
    parser.add_argument("infile", help="A three-field-per-line XYZ coordinate file to process")

    args = parser.parse_args(argv)

    return args, 0


def main(argv=None):
    """ Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != 0:
        return ret

    line_idx, min_coord, max_coord = process_infile(args.infile, args.bin_coordinate)
    bins, bin_idx = bin_data(line_idx, min_coord, max_coord, args.bin_size)
    write_results(bins, bin_idx, args.infile)

    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
