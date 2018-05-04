#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages

setup(name='mra',
      version='0.0.2',
      description='Minimalist RESTful Automation framework. Built for expandability and minimal configuration.',
      author='Drex',
      author_email='aeturnum@gmail.com',
      packages=find_packages(exclude=['tests']),
      install_requires=[
          "json5",
          'aiosqlite',
          'aiohttp',
          'beautifulsoup4',
          'jsonpickle',
          'tqdm'
      ],
      license="MIT",
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.6',
      ],
      python_requires=">=3.6",
      entry_points={
          'console_scripts': [
              'mra = mra.__main__:main'
          ]
      }
     )