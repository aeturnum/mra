#!/usr/bin/env python

from distutils.core import setup

setup(name='MRA',
      version='0.1',
      description='Minimalist RESTful Automation framework',
      author='Drex',
      author_email='aeturnum@gmail.com',
      packages=['mra'],
      license="MIT",
      entry_points={
          'console_scripts': [
              'mra = mra.__main__:main'
          ]
}
     )