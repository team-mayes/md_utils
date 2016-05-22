#!/usr/bin/env python
"""
To prepare for EVBFit:
Read cp2k force output files
--There are three sections, all starting with "ATOMIC FORCES in [a.u.]"
----The first is MM only
----The second is QM only
----The third is QMMM
--Keep only the third section, and reprint after converting from [a.u.] to kcal/mol
----1 a.u. force = 8.2387225(14)x10-8 N ; 1 J / m = 1 N  ; 1.0e-10 m = 1 A ;
                   6.022140857E+23 particles / mol ; 1 kcal = 4.1484 J
--- Thus, 1185.820922 a.u. force = 1 kcal/mol
"""

from __future__ import print_function
import os
import re
import sys
import argparse

import numpy as np

from md_utils.md_common import InvalidDataError, warning, create_out_fname, list_to_file


__author__ = 'hmayes'

# Error Codes
# The good status code
GOOD_RET = 0
INPUT_ERROR = 1
IO_ERROR = 2
INVALID_DATA = 3

# Constants #
au_to_N = 1185.820922

# # Config File Sections
# MAIN_SEC = 'main'
#
# # Config keys
# DUMPS_FILE = 'dump_list_file'


# # Defaults
DEF_FILE_LIST = 'cp2k_force_list.txt'
OUT_FILE_PREFIX = 'REF_'
DEF_OUT_DIR = None

OUT_FORMAT = '%d %.3f%.3f%.f'


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Reads in a list of cp2k output force files. For each file, '
                                                 'prints the 3rd set of forces only (combined QMMM) converted '
                                                 'from a.u. force units to kcal/mol-Angstrom. These files '
                                                 'have no headers. The first column is the atom index followed'
                                                 'by the forces in the x, y, and z directions.')
    parser.add_argument("-l", "--file_list", help="The location of the text file that list cp2k output files to "
                                                  "process. The default file name is {}, located in the base "
                                                  "directory where the program as run.".format(DEF_FILE_LIST),
                        default=DEF_FILE_LIST, )
    parser.add_argument("-d", "--out_dir", help="Directory for output files. The default option is the same location "
                                                "as the cp2k output file.",
                        default=DEF_OUT_DIR, )

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        warning(e)
        parser.print_help()
        return [], INPUT_ERROR

    if not os.path.isfile(args.file_list):
        if args.file_list == DEF_FILE_LIST:
            warning("Default file listing of cp2k force files missing: '{}'".format(DEF_FILE_LIST))
        else:
            warning("Specified file listing cp2k force files missing: '{}'".format(args.file_list))
        parser.print_help()
        return [], INPUT_ERROR

    if args.out_dir:
        if not os.path.isdir(args.out_dir):
            warning("Cannot find specified output directory: '{}'".format(args.out_dir))
            parser.print_help()
            return [], INPUT_ERROR

    return args, GOOD_RET


def process_cp2k_force_file(f_file, out_dir):
    """

    @param f_file: cp2k force output file to read and process (convert last section to kcal/(mol-Angstrom) )
    @param out_dir: where to create the new output file (last section, converted)
    @return: if a valid cp2k file, return a string with the total number of atoms and converted total forces
    """
    forces_pat = re.compile(r"^ATOMIC FORCES in .*")
    comment_pat = re.compile(r"^#.*")
    sum_pat = re.compile(r"^SUM.*")

    force_count = 0
    keep_lines = False
    line_count = 0
    to_print = []

    with open(f_file) as f:
        print('Reading file {}'.format(f_file))
        atom_num = None
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            if forces_pat.match(line):
                force_count += 1
                if force_count == 3:
                    keep_lines = True
            elif keep_lines:
                line_count += 1
                split_line = line.split()
                if comment_pat.match(split_line[0]):
                    continue
                try:
                    if sum_pat.match(split_line[0]):
                        sums = np.asarray(map(float, split_line[4:])) * au_to_N
                        if len(sums) != 4:
                            raise InvalidDataError("Did not find the expected four force values (x, y, z, total)")
                        # sums_str = ' '.join([str(atom_num)] + ['%8.3f'%F for F in sums])
                        f_out = create_out_fname(f_file, prefix=OUT_FILE_PREFIX, base_dir=out_dir, ext='')
                        list_to_file(to_print, f_out)
                        return np.append([atom_num], sums)
                except (ValueError, InvalidDataError) as e:
                    warning("{}\n"
                            "Check file: {}\n"
                            "   Line 'SUM OF ATOMIC FORCES' in the third 'ATOMIC FORCES' section: {}\n"
                            "Continuing to the next line in the file list".format(e, f_file, line))
                    return None

                try:
                    if len(split_line) != 6:
                        raise InvalidDataError("Did not find six expected values (Atom Kind Element X Y Z)")
                    atom_num = int(split_line[0])
                    # kind = int(split_line[1])
                    # element = split_line[2]
                    xyz = np.asarray(map(float, split_line[3:])) * au_to_N
                    to_print.append([atom_num] + xyz.tolist())
                except (ValueError, InvalidDataError) as e:
                    warning("{}\n"
                            "Check file: {}\n"
                            "  line {} in the third 'ATOMIC FORCES' section: {}\n"
                            "Continuing to the next line in the file list".format(e, f_file, line_count, line))
                    return None
    warning("Invalid file: {}\n"
            "Reached end of file without encountering a third 'SUM OF ATOMIC FORCES' section. "
            "Continuing to the next line in the file list.".format(f_file))
    return None


def read_file_list(file_list, out_dir):
    """
    @param file_list: the list of files to be read
    """
    summary_header = ['num_atoms', 'sum_x', 'sum_y', 'sum_z', 'total']
    summary_array = None

    with open(file_list) as f:
        for f_file in f:
            f_file = f_file.strip()
            if len(f_file) == 0:
                continue
            elif os.path.isfile(f_file):
                summary = process_cp2k_force_file(f_file, out_dir)
                if summary is not None:
                    if summary_array is None:
                        summary_array = summary
                    else:
                        summary_array = np.vstack((summary, summary_array))
            else:
                warning('Could not read file {} in file list {}. '
                        'Continuing to the next line in file list.'.format(f_file, file_list))
    # print(np.amax(summary_array, axis=1))
    if summary_array is None:
        warning("No valid cp2k force output files were read.")
    elif summary_array.size == 5:
        print('For the one CP2K force file read:')
        print(' ' + '      '.join(summary_header))
        print(' '.join(['%10.0f' % summary_array[0]] + ['%10.3f' % F for F in summary_array[1:]]))
    else:
        f_out = create_out_fname(file_list, prefix='force_sums_', base_dir=out_dir, ext='.csv')
        list_to_file(summary_array, f_out)
        with open(f_out, 'w') as logfile:
            logfile.write(','.join(summary_header) + "\n")
            for line in summary_array:
                logfile.write(','.join(['%d' % line[0]] + ['%f' % F for F in line[1:]]) + "\n")
        print('Finished reading all cp2k force files. Printed each atomic force sum to: {}'.format(f_out))

        min_vals = np.amin(summary_array, axis=0)
        max_vals = np.amax(summary_array, axis=0)

        print('           ' + '      '.join(summary_header))
        print('min_vals: ' + ' '.join(['%10.0f' % min_vals[0]] + ['%10.3f' % F for F in min_vals[1:]]))
        print('max_vals: ' + ' '.join(['%10.0f' % max_vals[0]] + ['%10.3f' % F for F in max_vals[1:]]))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET:
        return ret

    # Read template and dump files

    try:
        read_file_list(args.file_list, args.out_dir)
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
