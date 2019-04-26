"""
Setup script.

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2018-11-15
"""

import os

from setuptools import find_packages
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import shaptools

def read(fname):
    """
    Utility function to read the README file. README file is used to create
    the long description.
    """

    return open(os.path.join(os.path.dirname(__file__), fname)).read()

VERSION = shaptools.__version__
NAME = "shaptools"
DESCRIPTION = "API to expose SAP HANA functionalities"

AUTHOR = "xarbulu"
AUTHOR_EMAIL = "xarbulu@suse.com"
URL = ""

LICENSE = "Apache-2.0"

CLASSIFIERS = [

]

SCRIPTS = []

DEPENDENCIES = read('requirements.txt').split()

PACKAGE_DATA = {}
DATA_FILES = []


SETUP_PARAMS = dict(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    long_description=read('README.md'),
    packages=find_packages(),
    package_data=PACKAGE_DATA,
    license=LICENSE,
    scripts=SCRIPTS,
    data_files=DATA_FILES,
    install_requires=DEPENDENCIES,
    classifiers=CLASSIFIERS,
)

def main():
    """
    Setup.py main.
    """

    setup(**SETUP_PARAMS)

if __name__ == "__main__":
    main()
