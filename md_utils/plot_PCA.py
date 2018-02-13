from __future__ import print_function
from pyemma.coordinates import source
import numpy as np
import os
import pyemma.coordinates as coor
import pyemma.msm as msm
import pyemma.plots as mplt
import argparse
import matplotlib.pyplot
import mdtraj as md
import json
import jsonpickle
import warnings
from glob import glob
import math
import csv
import sys
import time
from matplotlib.pyplot import show, xlabel, xlim, ylabel, ylim, axes, plot, subplot2grid
from md_utils.md_common import IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, InvalidDataError, create_out_fname, warning

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError

# Fixes issue with decoding jsonpickle object
import jsonpickle.ext.numpy as jsonpickle_numpy

# TRAJ = '/Users/xadams/XylE/InwardOccluded_glucose/namd/trial1/6.6.coor'
# TOP = '/Users/xadams/XylE/InwardOccluded_glucose/inoc_glucose.psf'
# TRAJ_GLOB = ''
IG_FILE = 'IG_indices_in.txt'
EG_FILE = 'EG_indices_in.txt'

DEF_IG_FILE = 'IG_indices.txt'
DEF_EG_FILE = 'EG_indices.txt'
DEF_TRAJ = '*dcd'
DEF_TOP = '../*psf'
DEF_NAME = 'PCA.png'

jsonpickle_numpy.register_handlers()

matplotlib.rcParams.update({'font.size': 12})


def save_figure(name, out_dir=None):
    # change these if wanted
    if out_dir == None:
        fig_dir = './'
    else:
        fig_dir = out_dir
    matplotlib.pyplot.savefig(fig_dir + '/' + name, bbox_inches='tight')


def com_distance(traj, indexfile):
    # this function accepts a trajectory and a file with two rows of
    # 0 indexed indices to compute the center of mass for
    with open(indexfile, newline='') as file:
        rows = csv.reader(file, delimiter=' ', quotechar='|')
        ind_list = []
        for row in rows:
            ind_list.append(row)
    indices = np.array(ind_list, int)
    fronthalf = indices[0, :]
    backhalf = indices[1, :]
    traj1 = traj.atom_slice(fronthalf)
    traj2 = traj.atom_slice(backhalf)
    com1 = md.compute_center_of_mass(traj1)
    com2 = md.compute_center_of_mass(traj2)

    n = com1.shape[0]
    distance = np.empty([n], float)
    for i in range(0, n):
        distance[i] = abs(np.linalg.norm(com1[i, :] - com2[i, :])) * 10
    return distance

def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Plot trajectory files projected onto EG and IG dimensions')
    parser.add_argument("-t", "--traj", help="Trajectory file or files for analysis.",
                        default=DEF_TRAJ)
    parser.add_argument("-p", "--top", help="Topology file for the given trajectory files.",
                        default=DEF_TOP)
    parser.add_argument("-e", "--egindices", help="File with the EG indices.",
                        default=DEF_EG_FILE)
    parser.add_argument("-i", "--igindices", help="File with the IG indices.", default=DEF_IG_FILE)
    parser.add_argument("-n", "--name", help="Name for the saved plot", default=DEF_NAME)
    parser.add_argument("-o", "--outdir", help="Directory to save the figure to, default is current directory.", default=None)

    args = None
    try:
        args = parser.parse_args(argv)
        files = [args.top, args.egindices, args.igindices]
        for file in files:
            if not os.path.isfile(file):
                raise IOError("Could not find specified file: {}".format(file))
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
### Choose input data here. Trajectories and corresponding topology file.
# start = time.time()
# Alex's happy trajectory files
# trajfile = glob('/Users/xadams/XylE/Protonated_xylose/namd/plots/*dcd')
# topfile = '/Users/xadams/XylE/Protonated_xylose/step5_assembly.xplor_ext.psf'

def plot_trajectories(traj, topfile, eg_file, ig_file, plot_name, out_dir=None):

    trajfile = glob(traj)
    t = md.load(trajfile, top=topfile)

    EGdistance = com_distance(t, eg_file)
    IGdistance = com_distance(t, ig_file)
    # mplt.plot_free_energy(EGdistance, IGdistance, avoid_zero_count=False, kT=2.479, cmap="winter", cbar_label="Free energy (kcal/mol)")
    mplt.plot_free_energy(EGdistance, IGdistance, avoid_zero_count=False, kT=2.479, cmap="winter", cbar_label=None,
                          cbar=False)

    # trajfile = glob('/Users/xadams/XylE/InwardOpen_deprotonated/namd/7.2.dcd')
    # topfile = '/Users/xadams/XylE/InwardOpen_deprotonated/step5_assembly.xplor_ext.psf'
    #
    # t = md.load(trajfile, top=topfile)
    # EGdistance = com_distance(t, 'EG_indices_in.txt')
    # IGdistance = com_distance(t, 'IG_indices_in.txt')
    # mplt.plot_free_energy(EGdistance, IGdistance, avoid_zero_count=False, kT=2.479, cmap="winter", cbar_label="Free energy (kcal/mol)")


    # subplot2grid((2,1),(0,0))
    # plot(EGdistance)
    # subplot2grid((2,1),(1,0))
    # plot(IGdistance)
    # show()

    ax = axes()
    ax.set_xlim(7.5, 15)
    ax.set_ylim(7, 17)
    ax.set_xlabel("EG Distance (A)")
    ax.set_ylabel("IG Distance (A)")

    # i_name = create_out_fname(plot_name, ext='.png')
    save_figure(plot_name, out_dir)
    print("Wrote file: {}".format(plot_name))
    # print("Took ", time.time()-start, "seconds to execute.")
    matplotlib.pyplot.close("all")

def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    try:
        plot_trajectories(args.traj, args.top, args.egindices, args.igindices, args.name, args.outdir)
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
