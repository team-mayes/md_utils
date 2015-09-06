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

requirements = [
    'argparse',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='md_utils',
    version=md_utils.__version__,
    description="Utility scripts for MD data",
    long_description=readme + '\n\n' + history,
    author="Heather Mayes",
    author_email='hmayes@hmayes.com',
    url='https://github.com/hmayes/md_utils',
    packages=[
        'md_utils',
    ],
    entry_points = {
        'console_scripts': [
            'fes_combo = md_utils.fes_combo:main',
            'wham_rad = md_utils.wham_rad:main',
            'wham_block = md_utils.wham_block:main',
            'calc_pka = md_utils.calc_pka:main',
        ],
    },
    package_dir={'md_utils':
                 'md_utils'},
    package_data = {
        'aimless': ['skel/*.*', 'skel/tpl/*.*', 'skel/input/*.*'],
    },
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='md_utils',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
