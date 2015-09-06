WHAM_BLOCK
==========

1. Have a bash script that creates a folder with input to WHAM
** Two-column space-separated text files
2. Creates a file that's an input to WHAM
3. Run WHAM

To get an error estimate, take a series of data points (each file is a series of data points)

TODO
----

Make a new set of files to send to WHAM.
* Use template to create an aggregated submit script

Submit Script
-------------

wham 1.00 6.00 50 0.0001 310.0 0 meta.$i PMF.$i > wham.$i.txt

WHAM_SPLIT
==========

* Create dirs named (total splits)_(part)
* Floor for modulo remainder

WHAM_POST_BLOCK
===============

* Read all parts for a given dir prefix
* WHAM output file format (PMF*)
** Also accept radial correction rad_PMF

Out format CSV with headers:

coordinates average_free_energy standard_deviation_free_energy

CALC_PKA
========

* Input is rad_PMF (use corr col (3))
** Plan for standard WHAM, too.
* Find local max (inc, then dec) (two back) (middle val is tgt)
* Up to local max, do math and add to sum
* Result is PKA: out to stdout
* Debug out local max value

