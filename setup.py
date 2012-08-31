# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(
    name="localist",
    version="0.1",
    install_requires=["lxml"],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'localist = localist.main:main'
        ]
    }
)
