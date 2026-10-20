"""
Setup file for hydraulic_infrastructure_realisation.
Use setup.cfg to configure your project.

This file was generated with PyScaffold 3.1.
PyScaffold helps you to put up the scaffold of your new Python project.
Learn more under: https://pyscaffold.org/
"""
from setuptools import setup, find_packages

requires = [
    "matplotlib",
    "pandas",
    "numpy",
    "seaborn",
    "simpy",
    "scipy",
    "xlrd",
    "openpyxl",
    "plotly",
    "nbformat>=4.2",
    "jinja2",
    "sphinx_rtd_theme",
]

extras_require = {
    "dask": ["dask[distributed,diagnostics]"],
    "testing": ["pytest", "pytest-cov"],
}

with open("README.md", "r") as des:
    long_description = des.read()

setup(
    author="Mark van Koningsveld and Joris den Uijl",
    author_email="m.vankoningsveld@tudelft.nl",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="OpenQTSim facilitates discrete event simulation of queues with a Kendall notation.",
    install_requires=requires,
    extras_require=extras_require,
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="Queueing Theory",
    name="openqtsim",
    packages=find_packages(include=["openqtsim", "openqtsim.*"]),
    url="https://github.com/TUDelft-CITG/OpenQTSim",
    version="v0.5.1",
    zip_safe=False,
)
