#!/usr/bin/env bash

if [[ $TRAVIS_OS_NAME == 'linux' ]]; then
    sudo apt-get update
    wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh -O miniconda.sh;
else
    wget https://repo.continuum.io/miniconda/Miniconda2-latest-MacOSX-x86_64.sh -O miniconda.sh;
fi