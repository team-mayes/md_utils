from __future__ import print_function
import os
import subprocess
import sys
import argparse
from pathlib import Path
from md_utils.fill_tpl import OUT_DIR, TPL_VALS, fill_save_tpl
from md_utils.md_common import IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, InvalidDataError, warning

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

__author__ = 'xadams'

DEF_TOP = ['../protein.psf', 'protein.psf', '../step5_assembly.xplor_ext.psf']
IF_FILES = ['../protein.psf', '../inoc_glucose.psf']
OF_FILES = ['protein.psf', 'protg.psf']
OUT_FILE = 'orientation_quat.log'
IN = 'in'
OUT = 'out'
CONFORMATIONS = [IN, OUT]
CV_OUTNAMES = ['quat', 'rev', 'full', 'full_double', 'gating', 'cartesian']
CV_TPLS = []

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
    parser.add_argument("-r", "--reverse", help="Flag for 2-domain quaternion analysis with inward reference structure",
                        action='store_true', default=False)
    parser.add_argument("-f", "--full", help="Flag for 12 helix quaternion analysis.", action='store_true',
                        default=False)
    parser.add_argument("-d", "--double", help="Flag for 12 helix quaternion analysis with both reference structures.",
                        action='store_true', default=False)
    parser.add_argument("-g", "--gating", help="Flag for 2-gating distance analysis.", action='store_true',
                        default=False)
    parser.add_argument("-c", "--cartesian", help="Flag for full cartesian measurement of all alpha carbons.",
                        action='store_true', default=False)
    parser.add_argument("--conf",
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
        for file in args.files:
            if os.path.isfile(file):
                if file.endswith('.psf'):
                    args.top = file
                else:
                    args.traj.append(file)
            else:
                raise IOError("Could not find specified file: {}".format(file))
        if not any(args.traj):
            raise InvalidDataError("No trajectory files provided.")
        args.analysis_flags = [args.quat, args.reverse, args.full, args.double, args.gating, args.cartesian]
        if not any(args.analysis_flags):
            raise InvalidDataError("Did not choose to output any CV. No output will be produced.")
        for flag, outname in zip(args.analysis_flags, CV_OUTNAMES):
            if flag:
                outfile = args.name + '_' + outname + '.log'
                if os.path.isfile(outfile):
                    raise InvalidDataError("{} exists. Please rename or delete this file, "
                                           "or select a different name.")
                else:
                    args.outfiles.append(outfile)

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

# def gen_CV_script(args):
#     # This will combine appropriate tcl scripts for a single, efficient vmd run
#     print('hello')

def analysis(argv):
    # Read in the home directory and common for reference files
    home = str(Path.home())
    common = os.environ("COMMON")

    # Determine reference files based on home directory and topology file
    if argv[0] in IF_FILES:
        CV_IN = home + '/bin/tcl_scripts/orientation_quat_inoc.in'
    elif argv[0] in OF_FILES:
        CV_IN = home + '/bin/tcl_scripts/orientation_quat_prot.in'
    else:
        print("Exception: Unsure which ref file to use")
        exit(3)

    subprocess.call(["vmd", "-e", "/home/xadams/bin/orientation_quat.tcl", argv.top, argv[1], "-args", CV_IN])


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    try:
        # gen_CV_script(args)
        fill_save_tpl()
        analysis(args)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except (ValueError, InvalidDataError) as e:
        warning("Problems reading data:", e)
        return INVALID_DATA


if __name__ == '__main__':
    status = main()
    sys.exit(status)
