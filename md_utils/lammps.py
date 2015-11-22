# coding=utf-8
import itertools
import math
from collections import OrderedDict

from md_utils.md_common import xyz_distance, InvalidDataError

# Constants #

MISSING_ATOMS_MSG = "Could not find lines for atoms ({}) in timestep {}"
TSTEP_LINE = 'ITEM: TIMESTEP'
ATOMS_LINE = 'ITEM: ATOMS'


# Logic #

def find_atom_data(lamf, atom_ids):
    """Searches and returns the given file location for atom data for the given IDs.

    :param lamf: The LAMMPS data file to search.
    :param atom_ids: The set of atom IDs to collect.
    :return: A nested dict of the atoms found keyed first by time step, then by atom ID.
    :raises: InvalidDataError If the file is missing atom data or is otherwise malformed.
    """
    tstep_atoms = OrderedDict()
    atom_count = len(atom_ids)

    with open(lamf) as lfh:
        tstep_id = None
        tstep_val = "(no value)"
        for line in lfh:
            if line.startswith(TSTEP_LINE):
                try:
                    tstep_val = next(lfh).strip()
                    tstep_id = int(tstep_val)
                except ValueError as e:
                    raise InvalidDataError(
                        "Invalid timestep value {}: {}".format(tstep_val, e))
            elif tstep_id is not None:
                atom_lines = find_atom_lines(lfh, atom_ids, tstep_id)
                if len(atom_lines) != atom_count:
                    missing_atoms_err(atom_ids, atom_lines, tstep_id)
                tstep_atoms[tstep_id] = atom_lines
                tstep_id = None

    return tstep_atoms


def find_atom_lines(lfh, atom_ids, tstep_id):
    """Collects the atom data for the given IDs, returning a dict keyed by atom
    ID with the atom value formatted as a six-element list containing:

    * Molecule ID (int)
    * Atom type (int)
    * Charge (float)
    * X (float)
    * Y (float)
    * Z (float)

    :param lfh: A filehandle for a LAMMPS file.
    :param atom_ids: The set of atom IDs to collect.
    :param tstep_id: The ID for the current time step.
    :return: A dict of atom lines keyed by atom ID (int).
    :raises: InvalidDataError If the time step section is missing atom data or
        is otherwise malformed.
    """
    found_atoms = {}
    atom_count = len(atom_ids)
    for line in lfh:
        if line.startswith(ATOMS_LINE):
            for aline in lfh:
                sline = aline.split()
                if len(sline) == 7 and int(sline[0]) in atom_ids:
                    pline = list(map(int, sline[:3])) + list(map(float, sline[-4:]))
                    found_atoms[pline[0]] = pline[1:]
                    if len(found_atoms) == atom_count:
                        return found_atoms
                elif aline.startswith(TSTEP_LINE):
                    missing_atoms_err(atom_ids, found_atoms, tstep_id)
    return found_atoms

# Exception Creators #


def missing_atoms_err(atom_ids, found_atoms, tstep_id):
    """Creates and raises an exception when the function is unable to find atom
    data for all of the requested IDs.

    :param atom_ids: The atoms that were requested.
    :param found_atoms: The collection of atoms found.
    :param tstep_id: The time step ID where the atom data was missing.
    :raises: InvalidDataError Describing the missing atom data.
    """
    missing = map(str, atom_ids.difference(found_atoms.keys()))
    raise InvalidDataError(MISSING_ATOMS_MSG.format(",".join(missing),
                                                    tstep_id))


