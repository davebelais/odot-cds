#!/usr/bin/env python3
"""
This script writes a requirements.txt file based on the package versions in
your virtual environment
"""
import os
from subprocess import getstatusoutput

REPOSITORY_DIRECTORY = os.path.dirname(
    os.path.dirname(
        __file__
    )
)
PACKAGE_NAME = REPOSITORY_DIRECTORY.split('/')[-1].split('\\')[-1]


def set_requirements(
    path: str = 'requirements.txt',
    environment: str = PACKAGE_NAME
) -> None:
    command = 'conda list -n %s --export > %s' % (environment, path)
    print(command)
    status, output = getstatusoutput(command)
    if status:
        raise OSError(output)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))
    ))
    set_requirements()