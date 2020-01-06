import os
import sys
import warnings
from subprocess import getstatusoutput

import distro
from setuptools import setup

setup(
    name='odot-cds',
    version="2018.0.1",
    description=(
        'Oregon Department of Transportation - Crash Data System'
    ),
    author='David Belais',
    author_email='david@belais.me',
    python_requires='>=3.7',
    packages=['odot_cds'],
    install_requires=[
        "sob>=0.1.33",
        "lxml>=4.4.2",
        "pandas>=0.25.3",
        "iso8601>=0.1.12",
        "distro"
    ],
    extras_require={
        "dev": [
            "setuptools-setup-versions>=0.0.27"
        ]
    }
)

# Install MDBTools on Mac and Linux
if os.name == 'posix':
    if sys.platform.startswith('darwin'):
        install_command = 'brew install mdbtools'
    elif distro.linux_distribution()[0] in ('ubuntu', 'debian'):
        install_command = 'sudo apt-get install mdbtools'
    else:
        install_command = 'sudo yum install mdbtools'
    status, output = getstatusoutput(install_command)
    if status:
        warnings.warn(
            'Could not install MDBTools:\n' +
            output
        )