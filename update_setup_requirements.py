#!/usr/bin/env python3.7
from setuptools_setup_versions import install_requires

# # Update `setup.py` to require currently installed versions of all packages
install_requires.update_setup(operator='>=')