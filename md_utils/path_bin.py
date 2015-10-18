# !/usr/bin/env python
# coding=utf-8

"""
Sorts the data in given XYZ input file into bins of the given interval, producing a VMD-formatted
file containing the average XYZ coordinate for each bin that contains two or more samples.  A
separate CSV-formatted log file is also produced, which provides the bin value, the number of
samples, and the average and standard deviation for X, Y, and Z.
"""
import argparse
import logging
import sys

__author__ = 'cmayes'

# Logging #
# logging.basicConfig(filename='fes_combo.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('path_bin')

# Constants #

COORDS = ['x', 'y', 'z']

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
    lines = []
    with open(infile) as xyzfile:
        for xyzline in xyzfile:
            xyz = xyzline.split()
            if len(xyz) != 3:
                logger.warn("Skipping '%d'-element input line '%s'",
                            len(xyz), xyzline)
                continue

            try:
                float_xyz = map(float, xyz)
            except ValueError as e:
                logger.warn("Skipping non-float input line '%s'",
                            xyzline)
                continue

            line_coord_val = float_xyz[coord_pos]

            if max_coord is None or line_coord_val > max_coord:
                max_coord = line_coord_val

            if min_coord is None or line_coord_val < min_coord:
                min_coord = line_coord_val

            lines.append(float_xyz)

    return lines, max_coord, min_coord

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


    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
