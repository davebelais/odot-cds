#!/usr/bin/env python3.7
"""
This script cleans up some temporary files created by setuptools, tox, and
pytest
"""

import shutil
import os
from subprocess import getstatusoutput

if __name__ == '__main__':
    package = __file__.split(
        '/' if '/' in __file__ else '\\'
    )[-2]
    for file_or_directory in (
        'dist',
        '%s.egg-info' % package,
        'build', '.tox', '.cache', 'venv', '.pytest_cache'
    ):
        if os.path.exists(file_or_directory):
            command = (
                'git rm -r -f --cached --ignore-unmatch "%s"' %
                file_or_directory
            )
            print(command)
            status, output = getstatusoutput(command)
            if status != 0:
                raise OSError(output)
            if os.path.exists(file_or_directory):
                shutil.rmtree(file_or_directory)
