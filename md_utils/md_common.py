# coding=utf-8

"""
Common methods for this project.
"""

from __future__ import print_function, division
# Util Methods #
import csv
import difflib
import glob
import logging
from datetime import datetime
import shutil
import errno
import collections
import fnmatch
from itertools import chain, islice

import math
import os
import sys
from shutil import copy2, Error, copystat
import six

BACKUP_TS_FMT = "_%Y-%m-%d_%H-%M-%S_%f"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_wham_rad')

# Constants #

# Boltzmann's Constant in kcal/mol Kelvin
BOLTZ_CONST = 0.0019872041


# Exceptions #

class MdError(Exception): pass


class InvalidDataError(MdError): pass


class NotFoundError(MdError): pass


# Calculations #


def calc_kbt(temp_k):
    """
    Returns the given temperature in Kelvin multiplied by Boltzmann's Constant.

    :param temp_k: A temperature in Kelvin.
    :return: The given temperature in Kelvin multiplied by Boltzmann's Constant.
    """
    return BOLTZ_CONST * temp_k


def xyz_distance(fir, sec):
    """
    Calculates the Euclidean distance between the two given
    coordinates (expected format is numbers as [x,y,z]).

    TODO: Consider adding numpy optimization if lib is present.

    :param fir: The first XYZ coordinate.
    :type name: list.
    :param sec: The second XYZ coordinate.
    :type state: list.
    :returns:  float -- The Euclidean distance between the given points.
    :raises: KeyError
    """
    return math.sqrt((fir[0] - sec[0]) ** 2 + (fir[1] - sec[1]) ** 2 + (fir[2] - sec[2]) ** 2)


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


# I/O #

def cmakedir(tgt_dir):
    """
    Creates the given directory and its parent directories if it
    does not already exist.

    Keyword arguments:
    tgt_dir -- The directory to create

    """
    if not os.path.exists(tgt_dir):
        os.makedirs(tgt_dir)
    elif not os.path.isdir(tgt_dir):
        raise NotFoundError("Resource %s exists and is not a dir" %
                            tgt_dir)


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


def list_to_file(list_val, fname):
    """
    Writes the list to the given file.

    :param list_val: The list to write.
    :param fname: The location of the file to write.
    """
    with open(fname, 'w') as myfile:
        for line in list_val:
            myfile.write(line + "\n")


def create_backup_filename(orig):
    base, ext = os.path.splitext(orig)
    now = datetime.now()
    return "".join((base, now.strftime(BACKUP_TS_FMT), ext))


def find_backup_filenames(orig):
    base, ext = os.path.splitext(orig)
    found = glob.glob(base + "*" + ext)
    try:
        found.remove(orig)
    except ValueError:
        # Original not present; ignore.
        pass
    return found


def silent_remove(filename):
    """
    Removes the target file name, catching and ignoring errors that indicate that the
    file does not exist.

    :param filename: The file to remove.
    """
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


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


def move_existing_file(floc):
    """
    Renames an existing file using a timestamp based on the move time.

    :param floc: The location to check.
    """
    if os.path.exists(floc):
        shutil.move(floc, create_backup_filename(floc))


def create_out_fname(src_file, prefix, base_dir=None, ext=None):
    """Creates an outfile name for the given source file.

    :param src_file: The file to process.
    :param prefix: The file prefix to prepend.
    :param base_dir: The base directory to use; defaults to `src_file`'s directory.
    :param ext: The extension to use instead of the source file's extension;
        defaults to the `sec_file`'s extension.
    :return: The output file name.
    """
    if base_dir is None:
        base_dir = os.path.dirname(src_file)

    if ext is None:
        tgt_file = src_file
    else:
        tgt_file = os.path.splitext(src_file)[0] + ext

    return os.path.abspath(
        os.path.join(base_dir, prefix + os.path.basename(tgt_file)))


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

def read_csv_header(src_file):
    """Returns a list containing the values from the first row of the given CSV
    file or None if the file is empty.

    :param src_file: The CSV file to read.
    :return: The first row or None if empty.
    """
    with open(src_file) as csvfile:
        for row in csv.reader(csvfile):
            return list(row)


def read_csv(src_file, data_conv=None, all_conv=None):
    """
    Reads the given CSV (comma-separated with a first-line header row) and returns a list of
    dicts where each dict contains a row's data keyed by the header row.

    :param src_file: The CSV to read.
    :param data_conv: A map of header keys to conversion functions.  Note that values
        that throw a TypeError from an attempted conversion are left as strings in the result.
    :param all_conv: A function to apply to all values in the CSV.  A specified data_conv value
        takes precedence.
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
                elif all_conv:
                    try:
                        sdict[skey] = all_conv(sval)
                    except ValueError as e:
                        logger.debug("Could not convert value "
                                     "'%s' from column '%s': '%s'.  Leaving as str",
                                     sval, skey, e)
                        sdict[skey] = sval
                else:
                    sdict[skey] = sval
            result.append(sdict)
    return result


def write_csv(data, out_fname, fieldnames, extrasaction="raise"):
    """
    Writes the given data to the given file location.

    :param data: The data to write.
    :param out_fname: The name of the file to write to.
    :param fieldnames: The sequence of field names to use for the header.
    :param extrasaction: What to do when there are extra keys.  Acceptable
        values are "raise" or "ignore".
    """
    with open(out_fname, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames, extrasaction=extrasaction)
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


def fmt_row_data(raw_data, fmt_str):
    """ Formats the values in the dicts in the given list of raw data using
    the given format string.

    :param raw_data: The list of dicts to format.
    :param fmt_str: The format string to use when formatting.
    :return: The formatted list of dicts.
    """
    fmt_rows = []
    for row in raw_data:
        fmt_row = {}
        for key, raw_val in row.items():
            fmt_row[key] = fmt_str.format(raw_val)
        fmt_rows.append(fmt_row)
    return fmt_rows


# Comparisons #

def diff_lines(floc1, floc2):
    difflines = []
    with open(floc1) as file1:
        with open(floc2) as file2:
            diff = difflib.ndiff(file1.read().splitlines(), file2.read().splitlines())
            for line in diff:
                if line.startswith('-'):
                    logger.debug(line)
                    difflines.append(line)
                elif line.startswith('+'):
                    logger.debug(line)
                    pass
    return difflines


# Data Structures #

def unique_list(alist):
    """ Creates an ordered list from a list of tuples or other hashable items.
    From https://code.activestate.com/recipes/576694/#c6
    """
    mmap = {}
    oset = []
    for item in alist:
        if item not in mmap:
            mmap[item] = 1
            oset.append(item)
    return oset
