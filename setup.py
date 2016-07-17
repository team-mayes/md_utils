#!/usr/bin/env python
# -*- coding: utf-8 -*-
import md_utils

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = ['argparse',
                'six',
                #  'numpy',
                ]

test_requirements = ['argparse',
                     'six',
                     'numpy',
                     ]

setup(
    name='md_utils',
    version=md_utils.__version__,
    description="Utility scripts for MD data",
    long_description=readme + '\n\n' + history,
    author="Team Mayes",
    author_email='hmayes@hmayes.com',
    url='https://github.com/cmayes/md_utils',
    packages=['md_utils',
              ],
    entry_points={'console_scripts': ['align_on_col = md_utils.align_on_col:main',
                                      'calc_pka = md_utils.calc_pka:main',
                                      'calc_split_avg = md_utils.calc_split_avg:main',
                                      'convert_cp2k_forces = md_utils.convert_cp2k_forces:main',
                                      'data2pdb = md_utils.data2pdb:main',
                                      'data_edit = md_utils.data_edit:main',
                                      'dump_edit = md_utils.dump_edit:main',
                                      'evb_get_info = md_utils.evb_get_info:main',
                                      'evbdump2data = md_utils.evbdump2data:main',
                                      'filter_col_data = md_utils.filter_col_data:main',
                                      'fes_combo = md_utils.fes_combo:main',
                                      'fitevb_setup = md_utils.fitevb_setup:main',
                                      'lammps_dist = md_utils.lammps_dist:main',
                                      'lammps_proc_data = md_utils.lammps_proc_data:main',
                                      'md_init = md_utils.md_init:main',
                                      'path_bin = md_utils.path_bin:main',
                                      'pdb_edit = md_utils.pdb_edit:main',
                                      'per_col_stats = md_utils.per_col_stats:main',
                                      'press_dups = md_utils.press_dups:main',
                                      'process_cv_file = md_utils.process_cv_file:main',
                                      'wham_block = md_utils.wham_block:main',
                                      'wham_rad = md_utils.wham_rad:main',
                                      'wham_split = md_utils.wham_split:main',
                                      ],
                  },
    package_dir={'md_utils': 'md_utils'},
    package_data={'md_utils': ['skel/*.*', 'skel/tpl/*.*', 'skel/input/*.*'], },
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='md_utils',
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: BSD License',
                 'Natural Language :: English',
                 "Programming Language :: Python :: 2",
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Topic :: Scientific/Engineering :: Chemistry',
                 ],
    test_suite='tests',
    tests_require=test_requirements
)
