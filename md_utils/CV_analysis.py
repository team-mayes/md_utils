from __future__ import print_function
import os
import subprocess
import sys
import argparse
import re
from pathlib import Path
from collections import OrderedDict
from md_utils.fill_tpl import OUT_DIR, TPL_VALS, fill_save_tpl
from md_utils.md_common import (IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, InvalidDataError,
                                warning, read_tpl)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

__author__ = 'xadams'

home = str(Path.home())

DEF_TOP = ['../protein.psf', 'protein.psf', '../step5_assembly.xplor_ext.psf']
IF_FILES = ['../protein.psf', '../inoc_glucose.psf']
OF_FILES = ['protein.psf', 'protg.psf']
OUT_FILE = 'orientation_quat.log'
IN = 'in'
OUT = 'out'
CONFORMATIONS = [IN, OUT]
CV_OUTNAMES = ['quat', 'full', 'full_double', 'gating', 'cartesian']
QUAT = home + '/CV_analysis/tcl_scripts/' + 'orientation_quat.tpl'
FULL = home + '/CV_analysis/tcl_scripts/' + 'orientation_full.tpl'
DOUBLE = home + '/CV_analysis/tcl_scripts/' + 'orientation_full_double.tpl'
CV_TPLS = [QUAT, FULL, DOUBLE]
CV_TPLS_OUT = ["orientation_quat.in", "orientation_full.in", "orientation_full_double.in"]
REF_FILE = 'reference_file'
REF_FILE_2 = 'reference_file_2'
IN_REF_FILE = 'eq_100ns_inocg.pdb'
OUT_REF_FILE = 'eq_100ns_protonated.pdb'
IN_REF_FILE_2 = 'in_100ns_inoc.pdb'
OUT_REF_FILE_2 = 'in_100ns_protonated.pdb'
TCL_FILES = ["orientation_quat.tcl", "orientation_full.tcl", "orientation_full_double.tcl"]

# TCL Patterns
CV_IN_PAT = re.compile(r"^cv configfile.*")
EXIT_PAT = re.compile(r"^exit.*")
BASENAME_PAT = re.compile(r"^set basename.*")


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    'argv' is a list of arguments, or 'None' for 'sys.argv[1:]".
    """

    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(
        description='Perform a specified number of CV analyses when given a topology and trajectory files.')
    parser.add_argument('files', metavar='files', type=str, nargs='+')
    # parser.add_argument("-l", "--list", help="File with list of trajectory files")
    parser.add_argument("-q", "--quat", help="Flag for 2-domain quaternion analysis.", action='store_true',
                        default=False)
    # parser.add_argument("-r", "--reverse", help="Flag for 2-domain quaternion analysis with inward reference structure",
    #                     action='store_true', default=False)
    parser.add_argument("-f", "--full", help="Flag for 12 helix quaternion analysis.", action='store_true',
                        default=False)
    parser.add_argument("-d", "--double",
                        help="Flag for 24-D analysis: 12 helix quaternion analysis with both reference structures.",
                        action='store_true', default=False)
    parser.add_argument("-g", "--gating", help="Flag for 2-gating distance analysis.", action='store_true',
                        default=False)
    parser.add_argument("--cartesian", help="Flag for full cartesian measurement of all alpha carbons.",
                        action='store_true', default=False)
    parser.add_argument("-c", "--conf",
                        help="Conformation of the topology. This is important for selecting the reference file. "
                             "Valid options are {}. This will supercede internal topology detection logic".format(
                            CONFORMATIONS), choices=CONFORMATIONS)
    parser.add_argument("-n", "--name",
                        help="Base name for output files. The type of analysis will be appended for each file.",
                        type=str, default="CV_analysis")
    parser.add_argument("-o", "--out_dir", help="Directory to write output files to. Default is current directory.",
                        type=str, default='.')

    args = None
    # TODO: add list processing if necessary
    try:
        args = parser.parse_args(argv)
        args.traj = []
        args.outfiles = []
        # Check files and assign to either topology or trajectory lists
        for file in args.files:
            if os.path.isfile(file):
                if file.endswith('.psf'):
                    args.top = file
                else:
                    args.traj.append(file)
            else:
                raise IOError("Could not find specified file: {}".format(file))
        # Check that trajectories and analysis options are provided
        if not any(args.traj):
            raise InvalidDataError("No trajectory files provided.")
        args.analysis_flags = [args.quat, args.full, args.double, args.gating, args.cartesian]
        if not any(args.analysis_flags):
            raise InvalidDataError("Did not choose to output any CV. No output will be produced.")
        # Check for files with same names as output to be generated
        for flag, outname in zip(args.analysis_flags, CV_OUTNAMES):
            if flag:
                outfile = args.name + '_' + outname + '.log'
                if os.path.isfile(outfile):
                    raise InvalidDataError("{} exists. Please rename or delete this file, "
                                           "or select a different name.")
                else:
                    args.outfiles.append(outfile)
        # If no topology file is given, search for defaults and stop when first file is found
        try:
            args.top
        except:
            args.top = None
            for file in DEF_TOP:
                if os.path.isfile(file):
                    args.top = file
                    break
        if not args.top:
            raise InvalidDataError("No topology file provided and no default file found.")
        # Logic to detect the conformation of the files provided.
        # Currently very specific to Alex's data structure!
        if 'inoc' in args.top or args.top == '../protein.psf':
            args.conf = 'in'
        elif 'protg' in args.top or 'protx' in args.top or args.top == 'protein.psf' or args.top == '../step5_assembly.xplor_ext.psf':
            args.conf = 'out'

        tpl_vals = OrderedDict()
        # TODO: Fix automatic detection of 'common' directory
        # common = os.environ["COMMON"]
        common = '/Users/xadams/XylE/common/'
        if args.conf == 'in':
            tpl_vals[REF_FILE] = common + IN_REF_FILE
            tpl_vals[REF_FILE_2] = common + IN_REF_FILE_2
        elif args.conf == 'out':
            tpl_vals[REF_FILE] = common + OUT_REF_FILE
            tpl_vals[REF_FILE_2] = common + OUT_REF_FILE_2
        else:
            raise InvalidDataError("Conformation was not provided and could not be inferred from topology file {}. "
                                   "Please provide one of the following conformations: {}".format(args.top,
                                                                                                  CONFORMATIONS))
        args.config = {OUT_DIR: args.out_dir, TPL_VALS: tpl_vals, OUT_FILE: args.name}
        args.tpl_files = []
        args.tpl_names = []
        args.tcl_files = []
        global home
        for flag, tpl_in, tpl_out, tcl in zip(args.analysis_flags, CV_TPLS, CV_TPLS_OUT, TCL_FILES):
            if flag:
                args.tpl_files.append(tpl_in)
                args.tpl_names.append(tpl_out)
                args.tcl_files.append(home + '/CV_analysis/tcl_scripts/' + tcl)
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except (KeyError, InvalidDataError, SystemExit) as e:
        if hasattr(e, 'code') and e.code == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


def gen_CV_script(in_files, out_file, out_dir):
    # This will combine appropriate tcl scripts for a single, efficient vmd run
    i = 1

    with open(out_file, "w") as fout:
        for file in in_files:
            with open(file, "rt") as fin:
                for line in fin:
                    if CV_IN_PAT.match(line):
                        fout.write("cv configfile [lindex $argv {}]\n".format(i))
                    elif EXIT_PAT.match(line):
                        i += 1
                    elif BASENAME_PAT.match(line):
                        fout.write("set basename [lindex $argv 0]\n")
                    else:
                        fout.write(line)
        fout.write("exit")


def analysis(top, traj, tcl, base_output, in_files):
    # TODO: remove dispdev for use on remote clusters
    subprocess.call(
        ["vmd", "-e", tcl, top, ' '.join(traj), "-dispdev", "text", "-args", base_output, ' '.join(in_files)])


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    try:
        tcl_script = args.out_dir + '/' + 'CV_analysis.tcl'
        out_file = args.out_dir + '/' + args.name
        args.IN_FILES = []
        for file, name in zip(args.tpl_files, args.tpl_names):
            args.IN_FILES.append(args.out_dir + '/' + name)
            fill_save_tpl(args.config, read_tpl(file), args.config[TPL_VALS], file, name)
        gen_CV_script(args.tcl_files, tcl_script, args.out_dir)
        analysis(args.top, args.traj, tcl_script, out_file, args.IN_FILES)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except (ValueError, InvalidDataError) as e:
        warning("Problems reading data:", e)
        return INVALID_DATA


if __name__ == '__main__':
    status = main()
    sys.exit(status)
