from __future__ import print_function
import os
import subprocess
import sys
import argparse
from pathlib import Path
from md_utils.md_common import IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, InvalidDataError

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

__author__ = 'xadams'

DEF_TOP = ['../protein.psf','protein.psf','../step5_assembly.xplor_ext.psf']
IF_FILES = ['../protein.psf', '../inoc_glucose.psf']
OF_FILES = ['protein.psf', 'protg.psf']
OUT_FILE = 'orientation_quat.log'

def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    'argv' is a list of arguments, or 'None' for 'sys.argv[1:]".
    """

    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Perform a specified number of CV analyses.')
    parser.add_argument("-q" "--quat", help="Flag for 2-domain quaternion analysis.", action='store_true', default=False)
    parser.add_argument("-r" "--reverse", help="Flag for 2-domain quaternion analysis with inward reference structure", action='store_true', default=False)
    parser.add_argument("-f" "--full", help="Flag for 12 helix quaternion analysis.", action='store_true', default=False)
    parser.add_argument("-d" "--double", help="Flag for 12 helix quaternion analysis with both reference structures.", action='store_true', default=False)
    parser.add_argument("-g" "--gating", help="Flag for 2-gating distance analysis.", action='store_true', default=False)
    parser.add_argument("-c" "--cartesian", help="Flag for full cartesian measurement of all alpha carbons.", action='store_true', default=False)

    args = None
    try:
        args = parser.parse_args(argv)
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

# # Read in the home directory
# home = str(Path.home())
#
# # Read in command line arguments
# argv = sys.argv[1:]
# arg_num = len(argv[:])
#
# # Check that the outputfile will not overwrite existing file
# if os.path.isfile(OUT_FILE):
#   print("{} already exists, please rename or delete file.".format(OUT_FILE))
#   exit(2)
#
# # Exit for no arguments, for one argument search for default topology files
# if arg_num < 1:
#   print("No arguments provided. Please include a psf and coordinate/trajectory file.")
#   exit(2)
# elif arg_num == 1:
#   for TOP in DEF_TOP:
#     if os.path.isfile(TOP):
#       argv.append(argv[0])
#       argv[0] = TOP
#       break
# if arg_num < 2:
#     print("Insufficient arguments provided, please supply topology and trajectory file")
#     exit(2)
# # Determine reference files based on home directory and topology file
# if argv[0] in IF_FILES:
#     CV_IN = home + '/bin/tcl_scripts/orientation_quat_inoc.in'
# elif argv[0] in OF_FILES:
#     CV_IN = home + '/bin/tcl_scripts/orientation_quat_prot.in'
# else:
#     print("Exception: Unsure which ref file to use")
#     exit(3)
#
# subprocess.call(["vmd", "-e", "/home/xadams/bin/orientation_quat.tcl", argv[0], argv[1], "-args", CV_IN])

def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

if __name__ == '__main__':
    status = main()
    sys.exit(status)
