# coding=utf-8

"""
Common methods for this project.
"""

from __future__ import print_function, division
# Util Methods #
import csv
import logging
import fnmatch
from itertools import chain, islice

import os
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_wham_rad')

# Constants #

# Boltzmann's Constant in kcal/mol Kelvin
BOLTZ_CONST = 0.0019872041

# Calculations #

def calc_kbt(temp_k):
    """
    Returns the given temperature in Kelvin multiplied by Boltzmann's Constant.

    :param temp_k: A temperature in Kelvin.
    :return: The given temperature in Kelvin multiplied by Boltzmann's Constant.
    """
    return BOLTZ_CONST * temp_k

# Other #

def swarn(tgt=sys.stderr, *objs):
    """Writes a warning message to a target (stderr by default).
    :param tgt: The target to write to (stderr by default).
    :param objs: The elements of the message to write.
    """
    print("WARNING: ", *objs, file=tgt)


def chunk(seq, chunksize, process=iter):
    """Yields items from an iterator in iterable chunks.
    From https://gist.github.com/ksamuel/1275417

    :param seq: The sequence to chunk.
    :param chunksize: The size of the returned chunks.
    :param process: The function to use for creating the iterator.  Useful for iterating over different
    data structures.
    :return: Chunks of the given size from the given sequence.
    """
    it = iter(seq)
    while True:
        yield process(chain([it.next()], islice(it, chunksize - 1)))

# I/O #


def create_out_fname(src_file, prefix, base_dir=None):
    """Creates an outfile name for the given source file.

    :param src_file: The file to process.
    :param prefix: The file prefix to prepend.
    :param base_dir: The base directory to use; defaults to `src_file`'s directory
    :return: The output file name.
    """
    if base_dir is None:
        base_dir = os.path.dirname(src_file)

    return os.path.abspath(os.path.join(base_dir,
                                        prefix + os.path.basename(src_file)))


def find_files_by_dir(tgt_dir, pat):
    """Recursively searches the target directory tree for files matching the given pattern.
    The results are returned as a dict with a list of found files keyed by the absolute
    directory name.
    :param tgt_dir: The target base directory.
    :param pat: The file pattern to search for.
    :return: A dict where absolute directory names are keys for lists of found file names
        that match the given pattern.
    """
    matchdirs = {}
    for root, dirs, files in os.walk(tgt_dir):
        matches = [match for match in files if fnmatch.fnmatch(match, pat)]
        if matches:
            matchdirs[os.path.abspath(root)] = matches
    return matchdirs

# CSV #


def read_csv(src_file, data_conv=None):
    """
    Reads the given CSV (comma-separated with a first-line header row) and returns a list of
    dicts where each dict contains a row's data keyed by the header row.

    :param src_file: The CSV to read.
    :param data_conv: A map of header keys to conversion functions.  Note that values
        that throw a TypeError from an attempted conversion are left as strings in the result.
    :return: A list of dicts containing the file's data.
    """
    result = []
    with open(src_file) as csvfile:
        for sline in csv.DictReader(csvfile):
            sdict = {}
            for skey, sval in sline.items():
                if data_conv and skey in data_conv:
                    try:
                        sdict[skey] = data_conv[skey](sval)
                    except ValueError, e:
                        logger.debug("Could not convert value "
                                     "'%s' from column '%s': '%s'.  Leaving as str",
                                     sval, skey, e)
                        sdict[skey] = sval
                else:
                    sdict[skey] = sval
            result.append(sdict)
    return result


def write_csv(data, out_fname, fieldnames):
    """
    Writes the given data to the given file location.

    :param data: The data to write.
    :param out_fname: The name of the file to write to.
    :param fieldnames: The sequence of field names to use for the header.
    """
    with open(out_fname, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writeheader()
        writer.writerows(data)

# Conversions #


def str_to_bool(s):
    """
    Basic converter for Python boolean values written as a str.
    :param s: The value to convert.
    :return: The boolean value of the given string.
    :raises: ValueError if the string value cannot be converted.
    """
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError("Cannot covert {} to a bool".format(s))
