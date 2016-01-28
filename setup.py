#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Copyright (c) 2016, The Bioverse Development Team
#
# Distributed under the terms of the ISC License
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from setuptools import setup
from glob import glob

__version__ = "0.0.1-dev"


classes = """
    Development Status :: 3 - Alpha
    License :: OSI Approved :: ISC License (ISCL)
    Topic :: Scientific/Engineering :: Bio-Informatics
    Topic :: Software Development :: Libraries :: Application Frameworks
    Topic :: Software Development :: Libraries :: Python Modules
    Programming Language :: Python
    Programming Language :: Python :: 2.7
    Programming Language :: Python :: Implementation :: CPython
    Operating System :: POSIX :: Linux
    Operating System :: MacOS :: MacOS X
"""

with open('README.md') as f:
    long_description = f.read()

classifiers = [s.strip() for s in classes.split('\n') if s]

setup(name='bioverse',
      version=__version__,
      long_description=long_description,
      license="ISCL",
      description='Bioverse',
      author="Bioverse Development Team",
      author_email="bioverse.help@gmail.com",
      url='https://github.com/bioverse/bioverse',
      test_suite='nose.collector',
      packages=['bioverse'],
      scripts=glob('scripts/*'),
      extras_require={'test': ["nose", "flake8"]},
      install_requires=['django == 1.9.1'],
      classifiers=classifiers
      )
