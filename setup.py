#!/usr/bin/env python
"""
pip-safe
==========
.. code:: shell
  $ pip-safe install <foo>
  $ pip-safe list
  $ pip-safe remove <foo>
"""
import sys

from setuptools import find_packages, setup
import os

install_requires = ["pip", "tabulate", "six"]

if sys.version_info[0] == 2:
    install_requires.append("virtualenv")

tests_requires = ["pytest", "flake8"]

with open("README.md", "r") as fh:
    long_description = fh.read()

base_dir = os.path.dirname(__file__)

version = {}
with open(os.path.join(base_dir, "src", "pip_safe", "__about__.py")) as fp:
    exec(fp.read(), version)

setup(
    name="pip-safe",
    version=version["__version__"],
    author="Danila Vershinin",
    author_email="info@getpagespeed.com",
    url="https://github.com/dvershinin/pip-safe",
    description="A CLI tool to safely install CLI programs from PyPi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},  # Specify that the package is under the src directory
    packages=find_packages(where="src", exclude=["tests"]),
    zip_safe=False,
    license="BSD",
    install_requires=install_requires,
    extras_require={
        "tests": install_requires + tests_requires,
    },
    tests_require=tests_requires,
    include_package_data=True,
    entry_points={"console_scripts": ["pip-safe = pip_safe.main:main"]},
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
    ],
    # Exclude Python 3.0 through 3.3 due to venv not having with_pip option
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
)
