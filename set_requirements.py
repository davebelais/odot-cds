"""
This script writes a requirements.txt file based on the package versions in
your virtual environment
"""

from subprocess import getstatusoutput


def set_requirements(
    path: str = './requirements.txt',
    venv: str = './venv'
) -> None:
    status, output = getstatusoutput(
        venv + '/bin/pip3 freeze > ' + path
    )
    if status:
        raise OSError(output)


if __name__ == '__main__':
    set_requirements()