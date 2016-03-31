.. :changelog:

History
-------

0.7.1 (2016-03-31)
------------------

* Added dump_edit, pdb_edit, evbdump2data to distribution; these allow changes to, for example, the atom numbers


0.7.0 (2016-02-20)
------------------

* Added lammps_proc_data.py to calculate g(r) from a lammps dump file

0.6.0 (2015-11-22)
------------------

* Added lammps_dist to calculate atom pair distances as found in a LAMMPS dump file.


0.5.0 (2015-11-21)
------------------

* Added press_dups to compress CSV rows that have duplicate values for a given column.

0.4.2 (2015-10-24)
------------------

* Added path_bin for creating an averaged VMD file from a larger set of coordinates.

0.4.1 (2015-10-10)
------------------

* Added max_loc and max_val columns to calc_pka output.
* Fixed problem with 0-start files in fes_combo.

0.4.0 (2015-10-01)
------------------

* Changed `wham_rad` to set the zero point at the the largest CV free E, rather than the max CV

0.3.0 (2015-09-07)
------------------

* Added `wham_block.py`
* Added `wham_split.py`
* Refactored common code to `common` and `wham` modules.

0.2.0 (2015-09-03)
------------------

* Added `wham_rad.py`

0.1.0 (2015-09-01)
------------------

* Renamed to `md_utils`
* Added `fes_combo.py`

