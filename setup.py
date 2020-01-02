#!/usr/bin/env python
"""
pip-safe
==========
.. code:: shell
  $ pip-safe install <foo>
  $ pip-safe list
  $ pip-safe remove <foo>
"""

from setuptools import find_packages, setup
import os

install_requires = ["virtualenv", 'pip', 'tabulate', 'six']
tests_requires = ['pytest', 'flake8']

with open("README.md", "r") as fh:
    long_description = fh.read()

base_dir = os.path.dirname(__file__)

version = {}
with open(os.path.join(base_dir, "pip_safe", "__about__.py")) as fp:
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
    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
    license="BSD",
    install_requires=install_requires,
    extras_require={
        "tests": install_requires + tests_requires,
    },
    tests_require=tests_requires,
    include_package_data=True,
    entry_points={"console_scripts": ["pip-safe = pip_safe:main"]},
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
    ],
)
