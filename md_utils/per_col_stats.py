#!/usr/bin/env python
"""
Given a file with columns of data (space separated, no other data):
by default: returns the min, max, avg, and std dev per column
alternately: returns maximum x, y, and z coordinates, plus the values after a buffer length is added
"""

from __future__ import print_function

from md_utils.md_common import InvalidDataError, warning, np_float_array_from_file
import sys
import argparse

__author__ = 'hmayes'


# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3

# Constants #

# Defaults
DEF_ARRAY_FILE = 'qm_box_sizes.txt'


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in space-separated columns and returns the min, max, avg, and '
                                                 'std dev for each column.')
    parser.add_argument("-f", "--file", help="The location of the file with the dimensions with one line per vector, "
                                             "space-separated, containing at least two lines. The default file is {}, "
                                             "located in the current directory".format(DEF_ARRAY_FILE),
                        default=DEF_ARRAY_FILE)

    parser.add_argument("-b", "--buffer", help="If specified, the program will output only the max dimension"
                                               "in each column plus an additional buffer amount (float).",
                        default=None)

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


def process_file(data_file, len_buffer):
    dim_vectors = np_float_array_from_file(data_file)
    max_vector = dim_vectors.max(axis=0)
    print("Number of dimensions ({}) based on first line of file: {}".format(len(dim_vectors[0]), data_file))
    print("     Min value per column: {}".format(' '.join(['{:12.6f}'.format(x) for x in dim_vectors.min(axis=0)])))
    print("     Max value per column: {}".format(' '.join(['{:12.6f}'.format(x) for x in max_vector])))
    print("     Avg value per column: {}".format(' '.join(['{:12.6f}'.format(x) for x in dim_vectors.mean(axis=0)])))
    print("     Std. dev. per column: {}".format(' '.join(['{:12.6f}'.format(x) for x
                                                           in dim_vectors.std(axis=0, ddof=1)])))
    if len_buffer is not None:
        print("\nMax value plus {} buffer: {}".format(len_buffer,
                                                      ' '.join(['{:12.6f}'.format(x) for x in max_vector+len_buffer])))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET:
        return ret

    len_buffer = None
    try:
        if args.buffer is not None:
            try:
                len_buffer = float(args.buffer)
            except ValueError:
                raise InvalidDataError("Input for buffer ({}) could not be converted to a float.".format(args.buffer))
        process_file(args.file, len_buffer)
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
