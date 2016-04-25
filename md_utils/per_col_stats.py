#!/usr/bin/env python
"""
Given a file with columns of data (space separated, no other data):
by default: returns the min, max, avg, and std dev per column
alternately: returns maximum x, y, and z coordinates, plus the values after a buffer length is added
"""

from __future__ import print_function

from md_utils.md_common import InvalidDataError, warning, np_float_array_from_file, create_out_fname, list_to_file
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
DEF_DELIMITER = ' '

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

    parser.add_argument("-d", "--delimiter", help="Delimiter. Default is '{}'".format(DEF_DELIMITER),
                        default=DEF_DELIMITER)
                                            #       "Flag to indicate csv file. Default is a space-separated file with "
                                            # "only columns of numbers, and any header line preceded by a '#', as "
                                            # "created by numpy savetxt.",

    parser.add_argument("-n", "--names", help='File contains column names (header) (default is false).',
                        action='store_true')

    # parser.add_argument("-h", "--header", help="Flag to indicate that the file contains a header (default is false).",
    #                     action='store_true')
    #                                         #"Flag to indicate csv file. Default is a space-separated file with "
    #                                         # "only columns of numbers, and any header line preceded by a '#', as "
    #                                         # "created by numpy savetxt.",

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        warning(e)
        parser.print_help()
        return [], INPUT_ERROR

    return args, GOOD_RET


def process_file(data_file, len_buffer, delimiter, header=False):
    try:
        dim_vectors = np_float_array_from_file(data_file, delimiter=delimiter, header=header)
    except InvalidDataError as e:
        raise InvalidDataError("{}\n"
                               "Run program with '-h' to see options, such as specifying header row (-n) "
                               "and/or delimeter (-d)".format(e))

    max_vector = dim_vectors.max(axis=0)
    to_print = [['"Min value per column:"'] + dim_vectors.min(axis=0).tolist(),
                ['"Max value per column:"'] + max_vector.tolist(),
                ['"Avg value per column:"'] + dim_vectors.mean(axis=0).tolist(),
                ['"Std. dev. per column:"'] + dim_vectors.std(axis=0, ddof=1).tolist(),
                ]
    if len_buffer is not None:
        to_print.append(["Max value plus {} buffer:"] + (max_vector+len_buffer).tolist())

    print("Number of dimensions ({}) based on first line of file: {}".format(len(dim_vectors[0]), data_file))
    print("     Min value per column: {}".format(' '.join(['{:12.6f}'.format(x) for x in dim_vectors.min(axis=0)])))
    print("     Max value per column: {}".format(' '.join(['{:12.6f}'.format(x) for x in max_vector])))
    print("     Avg value per column: {}".format(' '.join(['{:12.6f}'.format(x) for x in dim_vectors.mean(axis=0)])))
    print("     Std. dev. per column: {}".format(' '.join(['{:12.6f}'.format(x) for x
                                                           in dim_vectors.std(axis=0, ddof=1)])))
    if len_buffer is not None:
        print("\nMax value plus {} buffer: {}".format(len_buffer,
                                                      ' '.join(['{:12.6f}'.format(x) for x in max_vector+len_buffer])))

    f_name = create_out_fname(data_file, prefix='stats_', ext='.csv')
    list_to_file(to_print, f_name, delimiter=',')
    print("Wrote file {}".format(f_name))

#
# with open('myfile.txt', 'r') as f:
#     first_line = f.readline()
# Some notes:
#
# As noted in the docs, unless it is the only line in the file, the string returned from f.readline() will contain a trailing newline. You may wish to use f.readline().strip()



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
        process_file(args.file, len_buffer, args.delimiter, header=args.names)
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
