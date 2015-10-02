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
from shutil import copy2, Error, copystat
import six

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


def swarn(*objs):
    """Writes a warning message to a target (stderr by default).
    :param objs: The elements of the message to write.
    """
    print("WARNING:", *objs, file=sys.stderr)


def swerr(*objs):
    """Writes an error message to a target (stderr by default).
    :param objs: The elements of the message to write.
    """
    print("ERROR:", *objs, file=sys.stderr)


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
        yield process(chain([six.next(it)], islice(it, chunksize - 1)))


# Stats #

# From http://stackoverflow.com/a/27758326

def mean(data):
    """Return the sample arithmetic mean of data."""
    n = len(data)
    if n < 1:
        raise ValueError('mean requires at least one data point')
    return sum(data) / n  # in Python 2 use sum(data)/float(n)


def _ss(data):
    """Return sum of square deviations of sequence data."""
    c = mean(data)
    ss = sum((x - c) ** 2 for x in data)
    return ss


def pstdev(data):
    """Calculates the population standard deviation."""
    n = len(data)
    if n < 2:
        raise ValueError('variance requires at least two data points')
    ss = _ss(data)
    pvar = ss / n  # the population variance
    return pvar ** 0.5


# I/O #


def file_to_str(fname):
    """
    Reads and returns the contents of the given file.

    :param fname: The location of the file to read.
    :return: The contents of the given file.
    :raises: IOError if the file can't be opened for reading.
    """
    with open(fname) as myfile:
        return myfile.read()


def str_to_file(str_val, fname):
    """
    Writes the string to the given file.

    :param str_val: The string to write.
    :param fname: The location of the file to write.
    """
    with open(fname, 'w') as myfile:
        myfile.write(str_val)


# TODO: Use this instead of duplicate logic in project.
def allow_write(floc, overwrite=False):
    """
    Returns whether to allow writing to the given location.

    :param floc: The location to check.
    :param overwrite: Whether to allow overwriting an exisiting location.
    :return: Whether to allow writing to the given location.
    """
    if os.path.exists(floc) and not overwrite:
        logger.warn("Not overwriting existing location '%s'", floc)
        return False
    return True


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


def copytree(src, dst, symlinks=False, ignore=None):
    """This is a copy of the standard Python shutil.copytree, but it
    allows for an existing destination directory.

    Recursively copy a directory tree using copy2().

    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    :param src: The source directory.
    :param dst: The destination directory.
    :param symlinks: Whether to follow symbolic links.
    :param ignore: A callable for items to ignore at a given level.
    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)

    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        # can't copy file access times on Windows
        if why.winerror is None:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error(errors)


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
                    except ValueError as e:
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
