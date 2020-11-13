"""
Setup file for hydraulic_infrastructure_realisation.
Use setup.cfg to configure your project.

This file was generated with PyScaffold 3.1.
PyScaffold helps you to put up the scaffold of your new Python project.
Learn more under: https://pyscaffold.org/
"""
import sys

from pkg_resources import require, VersionConflict
from setuptools import setup, find_packages

try:
    require('setuptools>=38.3')
except VersionConflict:
    print("Error: version of setuptools is too old (<38.3)!")
    sys.exit(1)

requires = [
    "matplotlib",
    "pandas",
    "numpy",
    "seaborn",
    "simpy",
    "scipy",
    "sphinx_rtd_theme"
]

setup_requirements = [
    "pytest-runner",
]

tests_require = [
    "pytest",
    "pytest-cov",
]

with open("README.md", "r") as des:
    long_description = des.read()

setup(
    author = "Mark van Koningsveld and Joris den Uijl",
    author_email = "m.vankoningsveld@tudelft.nl",
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description = "OpenQTSim facilitates discrete event simulation of queues with a Kendall notation.",
    install_requires = requires,
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data = True,
    keywords = "Queueing Theory",
    name = "openqtsim",
    packages = find_packages(include=["openqtsim"]),
    setup_requires = setup_requirements,
    test_suite = "tests",
    tests_require = tests_require,
    url = "https://github.com/TUDelft-CITG/OpenQTSim",
    version = "v0.5.0",
    zip_safe = False,
)