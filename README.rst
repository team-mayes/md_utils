============
MD Utilities
============

.. image:: https://img.shields.io/travis/cmayes/md_utils.svg
        :target: https://travis-ci.org/cmayes/md_utils

.. image:: https://img.shields.io/pypi/v/md_utils.svg
        :target: https://pypi.python.org/pypi/md_utils

.. image:: https://coveralls.io/repos/cmayes/md_utils/badge.svg?branch=master&service=github
        :target: https://coveralls.io/github/cmayes/md_utils?branch=master

Utility scripts for MD data

* Free software: BSD license
* Documentation: https://md_utils.readthedocs.org.

Scripts
-------

fes_combo
  Combines multiple FES output files into a single file so that the first
  column's value is sequential.  Files with higher starting index numbers
  are favored.

wham_split
  Breaks wham input into increasingly smaller blocks (divide initial data set
  by 2, then 3, 4...) and creates wham input (meta) files and submit scripts.

wham_rad
  Calculates the radially-corrected free energy values from WHAM output.

calc_pka
   From the wham_rad output, calculates the pKa.

