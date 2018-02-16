from __future__ import print_function
import numpy as np
import os
import pyemma.plots as mplt
import argparse
import matplotlib.pyplot as plt
import mdtraj as md
from glob import glob
import csv
import sys
import warnings
plt.switch_backend('agg')
from md_utils.md_common import IO_ERROR, GOOD_RET, INPUT_ERROR, INVALID_DATA, InvalidDataError, warning

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, NoSectionError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, NoSectionError

DEF_IG_FILE = 'IG_indices.txt'
DEF_EG_FILE = 'EG_indices.txt'
DEF_TRAJ = '*dcd'
DEF_TOP = '../*psf'
DEF_NAME = 'PCA.png'

plt.rcParams.update({'font.size': 12})

def save_figure(name, out_dir=None):
    # change these if wanted
    if out_dir == None:
        fig_dir = './'
    else:
        fig_dir = out_dir
    plt.savefig(fig_dir + '/' + name, bbox_inches='tight')


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
    parser.add_argument("-t", "--traj", help='Trajectory file or files for analysis. Wildcard arguments such as "*dcd" are permitted',
                        default=DEF_TRAJ)
    parser.add_argument("-p", "--top", help="Topology file for the given trajectory files.",
                        default=DEF_TOP)
    parser.add_argument("-e", "--egindices", help="File with the EG indices.",
                        default=DEF_EG_FILE)
    parser.add_argument("-i", "--igindices", help="File with the IG indices.", default=DEF_IG_FILE)
    parser.add_argument("-n", "--name", help="Name for the saved plot. Default name is {}".format(DEF_NAME), default=DEF_NAME)
    parser.add_argument("-o", "--outdir", help="Directory to save the figure to, default is current directory.", default=None)
    parser.add_argument("-l", "--log_file", help="Text file containing logged distances to plot.", default=None)
    parser.add_argument("-w", "--write_dist", help="Flag to log distances as a csv file rather than generate plot. Useful when dealing with large trajectories or limited memory.", action='store_true', default=False)

    args = None
    try:
        args = parser.parse_args(argv)
        # If a log file is read in, trajectory information is not required
        if not args.log_file:
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

def plot_trajectories(traj, topfile, eg_file, ig_file, plot_name, out_dir=None, log_file=None, write=False):

    if log_file:
        print("Reading data from log file: {}.".format(log_file))
        EG_list = []
        IG_list = []
        logging = 'eg'
        log = open(log_file)
        data = log.readlines()
        for row in data:
            s_data = row.split(sep=',')
            if logging=='eg':
                for i in s_data:
                    EG_list.append(i)
                logging = 'ig'
            else:
                for i in s_data:
                    IG_list.append(i)
                logging = 'eg'
        log.close()
        EGdistance = np.array(EG_list,float)
        IGdistance = np.array(IG_list,float)

        # with open(log_file, newline='\n') as file:
        #     rows = csv.reader(file, delimiter=',', quotechar='|')
        #     ind_list = []
        #     for row in rows:
        #         ind_list.append(row)
        #     indices = np.array(ind_list, float)
        #     EGdistance = np.empty([int(indices.size/2)])
        #     IGdistance = np.empty([int(indices.size/2)])
        #     for i in range(0,int(indices.shape[0]/2),1):
        #         EGdistance[int(i*indices.shape[1]):int((i+1)*indices.shape[1])] = indices[2*i, :]
        #         IGdistance[int(i*indices.shape[1]):int((i+1)*indices.shape[1])] = indices[2*i+1, :]

    else:
        #TODO: Restructure to more easily change to a different CV
        print("Reading data from trajectory: {}.".format(traj))
        trajfile = glob(traj)
        t = md.load(trajfile, top=topfile)

        EGdistance = com_distance(t, eg_file)
        IGdistance = com_distance(t, ig_file)

    if write:
        if out_dir == None:
            csv_dir = './'
        else:
            csv_dir = out_dir
        csv_name = csv_dir + '/' + plot_name + '.csv'
        with open(csv_name, 'a') as csvfile:
            dist_writer = csv.writer(csvfile, delimiter=',')
            dist_writer.writerow(EGdistance)
            dist_writer.writerow(IGdistance)
    else:
        ax = plt.axes()
        ax.set_xlim(7.5, 15)
        ax.set_ylim(7, 17)
        ax.set_xlabel("EG Distance (A)")
        ax.set_ylabel("IG Distance (A)")

        # Suppress the error associated with a larger display window than is sampled
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mplt.plot_free_energy(EGdistance, IGdistance, avoid_zero_count=False, ax=ax, kT=2.479, cmap="winter", cbar_label=None,
                                  cbar=False)

        save_figure(plot_name, out_dir)
        print("Wrote file: {}".format(plot_name + '.png'))
        plt.close("all")

def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)

    if ret != GOOD_RET or args is None:
        return ret

    try:
        plot_trajectories(args.traj, args.top, args.egindices, args.igindices, args.name, args.outdir, args.log_file, args.write_dist)
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
