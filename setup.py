# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in medtech_bpa/__init__.py
from medtech_bpa import __version__ as version

setup(
	name='medtech_bpa',
	version=version,
	description='Business Process Automation for MedTech',
	author='Indictrans',
	author_email='contact@indictranstech.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
