import os
import sys
from typing import Iterable

from setuptools import setup


setup(
    name='odot-cds',
    version="0.0.16",
    description=(
        'Oregon Department of Transportation - Crash Data System'
    ),
    author='David Belais',
    author_email='david.belais@kroger.com',
    python_requires='>=3.7',
    packages=['odot-cds'],
    install_requires=[
        'pandas'
    ]
)