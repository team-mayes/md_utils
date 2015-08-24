#!/usr/bin/env python
# -*- coding: utf-8 -*-
import raptor_utils

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
    name='raptor_utils',
    version=raptor_utils.__version__,
    description="Utility scripts for Raptor data",
    long_description=readme + '\n\n' + history,
    author="Heather Mayes",
    author_email='hmayes@hmayes.com',
    url='https://github.com/hmayes/raptor_utils',
    packages=[
        'raptor_utils',
    ],
    entry_points = {
        'console_scripts': [
            'fes_combo = raptor_utils.fes_combo:main',
        ],
    },
    package_dir={'raptor_utils':
                 'raptor_utils'},
    package_data = {
        'aimless': ['skel/*.*', 'skel/tpl/*.*', 'skel/input/*.*'],
    },
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='raptor_utils',
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
