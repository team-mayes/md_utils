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

import csv
import os
import re
import sys
import argparse
import numpy as np
from md_utils.md_common import (InvalidDataError, warning, create_out_fname, list_to_file, IO_ERROR, GOOD_RET,
                                INPUT_ERROR, INVALID_DATA, file_rows_to_list)

__author__ = 'hmayes'

# Constants #
au_to_N = 1185.820922

# # Defaults
DEF_FILE_LIST = 'cp2k_force_list.txt'
OUT_FILE_PREFIX = 'REF_'
DEF_OUT_DIR = None

OUT_FORMAT = '%d %.3f%.3f%.f'
F_NAME = "file_name"
NUM_ATOMS = "num_atoms"
FORCE_X = "force_x"
FORCE_Y = "force_y"
FORCE_Z = "force_z"
FORCE_TOT = "force_tot"
FORCE_TOT_UNITS = "total_force_kcal_per_mol"
STDOUT_HEADERS = [NUM_ATOMS, FORCE_X, FORCE_Y, FORCE_Z, FORCE_TOT]
SUM_FILE_HEADERS = [F_NAME, NUM_ATOMS, FORCE_X, FORCE_Y, FORCE_Z, FORCE_TOT_UNITS]


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
                        default=DEF_FILE_LIST)
    parser.add_argument("-f", "--file", help="The location of a single cp2k output file to process. This option "
                                             "take precedence over the file_list option.".format(DEF_FILE_LIST),
                        default=None, )
    parser.add_argument("-n", "--num_atoms", help="If specified, the program will only include files in the summary "
                                                  "which have the specified number of atoms.",
                        default=None, )
    parser.add_argument("-d", "--out_dir", help="Directory for output files. The default option is the same location "
                                                "as the cp2k output file.",
                        default=DEF_OUT_DIR, )

    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except SystemExit as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return [], INPUT_ERROR

    if args.file is None:
        args.file_name = args.file_list
        if os.path.isfile(args.file_list):
            args.file_list = file_rows_to_list(args.file_list)
        else:
            if args.file_list == DEF_FILE_LIST:
                warning("Default file listing of cp2k force files missing: '{}'".format(DEF_FILE_LIST))
            else:
                warning("Specified file listing cp2k force files missing: '{}'".format(args.file_list))
            parser.print_help()
            return args, INPUT_ERROR
    else:
        args.file_name = args.file
        if os.path.isfile(args.file):
            args.file_list = [args.file]
        else:
            warning("Missing specified file: {}".format(args.file))
            parser.print_help()
            return args, IO_ERROR

    if args.out_dir:
        if not os.path.isdir(args.out_dir):
            warning("Cannot find specified output directory: '{}'".format(args.out_dir))
            parser.print_help()
            return args, INPUT_ERROR

    if args.num_atoms is not None:
        try:
            args.num_atoms = int(args.num_atoms)
        except ValueError:
            warning("Could not convert specified num_atoms ('{}') to an integer."
                    "".format(args.num_atoms))
            parser.print_help()
            return args, INPUT_ERROR

    return args, GOOD_RET


def check_atom_num(req_atom_num, last_line, file_name):
    """
    If applicable, make sure read the expected number of atoms
    @param req_atom_num: None if not specified; otherwise an int
    @param last_line: the last line read before a summary section; the first number of that line
        identifies the number of atoms in the last section
    @param file_name: name of file used for error message
    @return: raise InvalidDataError() if did not find the required
    """
    if req_atom_num is not None:
        num_atoms = int(last_line.split()[0])
        if num_atoms != req_atom_num:
            raise InvalidDataError("Based on user specified num_atoms, expected to have read {} atoms, "
                                   "but read {} in file: {}".format(req_atom_num, num_atoms, file_name))


def process_cp2k_force_file(f_file, out_dir, req_atom_num):
    """
    Gathers and prints a list of data for converted force file (length = num atoms)
    Gathers summary data for the file; not as a dict but as a list because that helps data analysis
    Also checks how many times found the summary section; ideally, there are exactly 3. However, if the program
        did not complete a QMMM force calculations, it will not print 3 sections (MM, QM, and then QMMM).
        If the job is attempted more than once, CP2K will keep appending forces each time. It is possible that the
        MM section (and others) are repeated multiple times. There may be 3 sections that are all MM. There
        may be some combination of MM, QM, and QMMM outputs. CP2K does not identify the force calculation type.
        The logic here attempts to catch multiple MM outputs (assumes that QM and QMMM force summaries will not
        exactly match the MM force summary).

    @param f_file: cp2k force output file to read and process (convert last section to kcal/(mol-Angstrom) )
    @param out_dir: where to create the new output file (last section, converted)
    @param req_atom_num: An integer if specified by the user; otherwise None. If not None, use it to validate
      that found the expected number of atoms
    @return: if a valid cp2k file, return a np array with converted force summary.
       Otherwise, None
    """
    forces_pat = re.compile(r"^ATOMIC FORCES in .*")
    comment_pat = re.compile(r"^#.*")
    sum_pat = re.compile(r"^SUM.*")
    sum_pat_num = 0

    last_line = None
    md_sum = None
    qm_sum = None
    qmmm_sum = None
    qmmm_last_atom = None
    ready_to_read = False

    keep_lines = False
    to_print = []

    with open(f_file) as f:
        atom_num = None
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            if sum_pat.match(line):
                sum_pat_num += 1
                if md_sum is None:
                    md_sum = line
                    check_atom_num(req_atom_num, last_line, f_file)
                elif line == md_sum:
                    warning("Line matching the read MM summary encountered.")
                    if qm_sum is not None:
                        warning("QM section previous read; will be overwritten if found.")
                        qm_sum = None
                else:
                    if qm_sum is None:
                        qm_sum = line
                        ready_to_read = True
                    elif line == qm_sum:
                        raise InvalidDataError("Did not expect to read QM summary twice infile: {}".format(f_file))
                    else:
                        # should be at the third and last sum section
                        qmmm_sum = line
                        qmmm_last_atom = last_line

            elif forces_pat.match(line):
                if ready_to_read:
                    keep_lines = True
            elif keep_lines:
                split_line = line.split()
                if comment_pat.match(split_line[0]):
                    continue
                try:
                    if len(split_line) != 6:
                        raise InvalidDataError("Did not find six expected values (Atom Kind Element X Y Z)")
                    atom_num = int(split_line[0])
                    xyz = np.asarray(map(float, split_line[3:])) * au_to_N
                    # noinspection PyTypeChecker
                    to_print.append([atom_num] + xyz.tolist())
                except (ValueError, InvalidDataError) as e:
                    warning("{}\n"
                            "Check file: {}\n"
                            "  Problem reading line as atomic forces: {}\n"
                            "Continuing to the next line in the file list".format(e, f_file, line))
                    return None
            last_line = line
    if qmmm_sum is None:
        warning("Invalid file: {}\n"
                "Reached end of file without encountering the expected QMMM 'SUM OF ATOMIC FORCES' section "
                "(read {} summary force sections, checking for likely duplicate MM force output). "
                "Continuing to the next line in the file list.".format(f_file, sum_pat_num))
        return None
    try:
        check_atom_num(req_atom_num, qmmm_last_atom, f_file)
        split_line = qmmm_sum.split()
        sums = np.asarray(map(float, split_line[4:])) * au_to_N
        if len(sums) != 4:
            raise InvalidDataError("Did not find the expected four force values (x, y, z, total)")
        f_out = create_out_fname(f_file, prefix=OUT_FILE_PREFIX, base_dir=out_dir, ext='')
        list_to_file(to_print, f_out)
        return np.append([atom_num], sums)
    except (ValueError, InvalidDataError) as e:
        warning("{}\nCheck file: {}\n"
                "   Problem converting values in line: {}\n"
                "Continuing to the next line in the file list".format(e, f_file, qmmm_sum))
    return None


def process_file_list(file_name, file_list, out_dir, req_atom_num):
    """
    Reads the list of files and calls functions to process each file and to print the summary to a file and to
      standard out
    @param file_name: the path of the file used to specify input
    @param file_list: the list of files to be read
    @param out_dir: user-specified output directory
    @param req_atom_num: An integer if specified by the user; otherwise None. If not None, use it to validate
      that found the expected number of atoms
    """
    summary_array = None
    f_name_list = []

    for f_file in file_list:
        f_file = f_file.strip()
        if len(f_file) == 0:
            continue
        elif os.path.isfile(f_file):
            summary = process_cp2k_force_file(f_file, out_dir, req_atom_num)
            if summary is not None:
                f_name_list.append(os.path.basename(f_file))
                if summary_array is None:
                    summary_array = summary
                else:
                    summary_array = np.vstack((summary_array, summary))
        else:
            warning('Could not read file {} in file list {}. '
                    'Continuing to the next line in file list.'.format(f_file, file_list))

    if summary_array is None:
        warning("No valid cp2k force output files were read.")
    elif summary_array.size == 5:
        print('For the one CP2K force file read:')
        stdout_head_format = '{:>10s}' + ' {:>10}' * 4
        print(stdout_head_format.format(*STDOUT_HEADERS))
        print(' '.join(['%10.0f' % summary_array[0]] + ['%10.3f' % F for F in summary_array[1:]]))
    else:
        f_out = create_out_fname(file_name, prefix='force_sums_', base_dir=out_dir, ext='.csv')
        with open(f_out, 'w') as csv_file:
            writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows([SUM_FILE_HEADERS])
            for data_f_name, sum_data in zip(f_name_list, summary_array):
                writer.writerows([[data_f_name] + [int(sum_data[0])] + [round(num, 6) for num in sum_data[1:]]])
        print('Finished reading all cp2k force files. Printed each atomic force sum to: {}'.format(f_out))
        min_vals = np.amin(summary_array, axis=0)
        max_vals = np.amax(summary_array, axis=0)
        stdout_head_format = '{:>10s}' * 2 + ' {:>10}' * 4
        print(stdout_head_format.format('', *STDOUT_HEADERS))
        stdout_num_format = '{:10s}{:10.0f}' + ' {:10.3f}' * 4
        # noinspection PyArgumentList
        print(stdout_num_format.format('min_vals: ', *min_vals))
        # noinspection PyArgumentList
        print(stdout_num_format.format('max_vals: ', *max_vals))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    try:
        process_file_list(args.file_name, args.file_list, args.out_dir, args.num_atoms)
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
