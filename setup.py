from setuptools import setup

setup(
    name='odot-cds',
    version="2020.0.1",
    description=(
        'Oregon Department of Transportation - Crash Data System'
    ),
    author='David Belais',
    author_email='david@belais.me',
    python_requires='>=3.7',
    packages=['odot_cds'],
    install_requires=[
        "lxml>=4.4.2",
        "pandas>=0.25.3",
        "iso8601>=0.1.12"
    ],
    extras_require={
        "dev": [
            "setuptools-setup-versions>=0.0.28",
            "lxml>=4.4.2",
            "pandas>=0.25.3",
            "iso8601>=0.1.12"
        ],
        "test": [
            "setuptools-setup-versions>=0.0.28",
            "lxml>=4.4.2",
            "pandas>=0.25.3",
            "iso8601>=0.1.12"
        ]
    }
)