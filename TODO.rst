WHAM_BLOCK
==========

1. Have a bash script that creates a folder with input to WHAM
** Two-column space-separated text files
2. Creates a file that's an input to WHAM
3. Run WHAM

To get an error estimate, take a series of data points (each file is a series of data points)


WHAM_POST_BLOCK
===============

* Read all parts for a given dir prefix
* WHAM output file format (PMF*)
** Also accept radial correction rad_PMF
* To calculate the average and standard deviation
** read the (radial corrected) free energy for a given coordinate from each rad_PMF file for a given coordinate prefix
** output the coordiante, the average, and standard deviation (i.e. for directory 07_*, there are 8 files; the
coordinates will align for each file; read the 8 differing values for free E for that coordinate, calc the avg and st dev, and output

Out format CSV with headers:

coordinates average_free_energy standard_deviation_free_energy

File name

avg_rad_PMF.02.csv

CALC_PKA
========

* Input is rad_PMF (use corr col (3))
** Plan for standard WHAM, too.
* Find local max (inc, then dec) (two back) (middle val is tgt);
  in the algorithm below, I will call the coordinate points
  r_i-1 r_i, and r_i+1   (middle point, r_i, is the tgt);
  and for energy, corr_i-1, corr_i, and coor_i+1
* Up to local max, do math and add to sum
** Will need to calculate the spacing between coordinate values
  (called delta_r); usually this will be a constant number, but
  it is not in the case of your sample data because I deleted
  points. You can certainly calculate this every step if you wish,
  so we don't have to count on equal spacing; the calculation
  can be delta_r = r_i+1 - r_i
** we will need pi
** a new constant we can call inv_C_0 (that's a zero) = 1660.0
   (it's units are Angstrom ^ 3 / molecule )
** will will need kBT (you calculated this before, in wham_rad;
   you can have the user enter the temp. The temp will be the
   same as used in wham_rad and in making the wham input line
** sum_for_pka += 4.0 * pi * r_i ** 2 * math.exp( -corr_i / kBT ) * delta_r
** pKa = - math.log10 ( inv_C_0 / sum_for_pka )
* Result is PKA: out to stdout
* Debug out local max value

Questions
---------

* Did we intend to leave rad file as .txt as opposed to .csv?
