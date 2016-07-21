.. :changelog:

History
-------

0.9.1 (2016-07-20)
------------------

* Updated pdb_edit to fill in the element column of a pdb file (sometime VMD removes it). The program uses
a dictionary of atom_type,element based on CHARMM36. Users can specify a different mapping of PDB atom types to
element types.

0.9.0 (2016-07-17)
------------------

* Now uses the csv.QUOTE_NONNUMERIC option for writing and reading, to automatically convert to floats

0.8.2 (2016-06-22)
------------------

* Updated data_edit so that output is formatted into columns. Additionally, when comparing data files, lines that
differ only by more a specified tolerance (~1e-5) are now ignored.

0.8.1 (2016-06-14)
------------------

* Now correctly sorts differences between data files, ignoring comments, unimportant ordering...

0.8.0
------------------

* Added capabilty to data_edit: now will show differences between data files, ignoring comments, unimportant ordering...


0.7.3 (2016-04-20)
------------------

* Changed data_reorder to data_edit, reflecting its additional capabilities.

0.7.2 (2016-04-14)
------------------

* Added data2data, data_reorder to distribution

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

