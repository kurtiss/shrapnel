#!/usr/bin/env python
# encoding: utf-8
"""
setup.py

Created by Kurtiss Hare on 2010-08-05.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

from setuptools import setup, find_packages
import os

execfile(os.path.join('shrapnel', 'version.py'))

setup(
    name = 'shrapnel',
    version = VERSION,
    description = 'Shrapnel provides tools to make writing web apps with Tornado easier.',
    author = 'Kurtiss Hare',
    author_email = 'kurtiss@gmail.com',
    url = 'http://www.github.com/kurtiss/shrapnel',
    packages = find_packages(),
    scripts = [],
    classifiers = [
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    install_requires = [
#       'tornado',
#       'pymongo',
#       'memcache'
    ]
)