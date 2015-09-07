# coding=utf-8

"""
Common WHAM logic.
"""
import logging
import os

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wham')

# Keys #

# -Meta- #

LINES_KEY = "lines"
DIR_KEY = "dir"
LOC_KEY = "loc"

# -Radial Correction- #

CORR_KEY = 'corr'
COORD_KEY = 'coord'
FREE_KEY = 'free_energy'
RAD_KEY_SEQ = [COORD_KEY, FREE_KEY, CORR_KEY]


def read_meta(meta_file):
    """
    Reads the given meta file, returning the parsed value as a dict containing:

    * loc: A string with the original (possibly relative) location
    * dir: A string with absolute path for the directory containing the meta file.
    * lines: a list of four-element lists that represent each line in the meta file.

    :param meta_file: The meta file to parse.
    :return: The parsed contents of the meta file.
    """
    meta = {LOC_KEY: meta_file, DIR_KEY: os.path.dirname(os.path.abspath(meta_file))}
    lines = []
    with open(meta_file) as mfile:
        for mline in mfile:
            lines.append(mline.strip().split())
    meta[LINES_KEY] = lines
    return meta


def read_rmsd(fname):
    """
    Reads the RMSD file at the given file name.

    :param fname: The file's location.
    :return: The values in the RMSD file.
    """
    rmsd_values = []
    with open(fname) as rfile:
        row_val = None
        for rline in rfile:
            try:
                row_val = rline.split()[1]
                rmsd_values.append(float(row_val))
            except IndexError:
                logger.warn("RMSD Line '%s' did not have two fields", rline)
            except TypeError:
                logger.warn("RMSD Value '%s' is not a float", row_val)
    return rmsd_values


def read_meta_rmsd(meta):
    """
    Finds and parses the RMSD files described in the given parsed meta file's contents.

    :param meta: The result of calling read_meta with a meta file location.
    :return: A dict of lists containing floats for each line in each found RMSD file
        keyed by the RMSD file name (no directory info is included in the key)
    """
    rmsd_data = {}
    for line in meta[LINES_KEY]:
        rmsd_fname = os.path.basename(line[0])
        floc = os.path.join(meta[DIR_KEY], line[0])
        rmsd_data[rmsd_fname] = read_rmsd(floc)
    return rmsd_data


def write_rmsd(tgt_dir, rmsd, overwrite=False):
    """
    Writes out all of the described RMSD files into the given target directory.

    :param tgt_dir: The data where the files will go.
    :param rmsd: A dict of an array of floats keyed by file name.
    :param overwrite: Whether to overwrite existing files.
    """
    for rmsd_fname, data in rmsd.items():
        tgt_file = os.path.join(tgt_dir, rmsd_fname)
        if os.path.exists(tgt_file) and not overwrite:
            logger.warn("Not overwriting existing RMSD file '%s'", tgt_file)
            continue
        with open(tgt_file, 'w') as wfile:
            for i, rmsd_val in enumerate(data, 1):
                wfile.write("\t".join((str(i), str(rmsd_val))))
                wfile.write("\n")


def write_meta(tgt_dir, meta, step, overwrite=False):
    """
    Writes out the meta file using the original meta data structure as a beginning.

    :param tgt_dir: The target directory for the meta file.
    :param meta: The parsed data from the original meta file.
    :param step: The step number being processed.
    :param overwrite: Whether to overwrite an existing meta file.
    """
    step_meta = "meta.{:02d}".format(step)
    meta_tgt = os.path.join(tgt_dir, step_meta)
    if os.path.exists(meta_tgt) and not overwrite:
        logger.warn("Not overwriting existing meta file '%s'", meta_tgt)
        return
    with open(meta_tgt, 'w') as mfile:
        for mline in meta[LINES_KEY]:
            rmsd_loc = os.path.join("{:02d}".format(step),
                                    os.path.basename(mline[0]))
            mfile.write(rmsd_loc)
            mfile.write('\t')
            mfile.write('\t'.join(mline[1:]))
            mfile.write('\n')
