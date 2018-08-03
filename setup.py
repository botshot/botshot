# -*- coding: utf-8 -*-

import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='botshot',
    version='0.90-beta',
    packages=find_packages(),
    include_package_data=True,
    license='GPL',
    description='A framework for creating stateful chatbots on Django.',
    long_description=README,
    url='https://github.com/prihoda/botshot',
    author='David Příhoda, Matúš Žilinec, Jakub Drdák',
    author_email='david.prihoda@gmail.com, zilinec.m@gmail.com',
    entry_points={
          'console_scripts': [
              'bots = bots:main'
          ]
      },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Communications :: Chat',
    ],
    install_requires=['django>=2.0.0', 'networkx', 'requests', 'six', 'sqlparse', 'wit==4.3.0', 'wheel', 'redis',
                      'pytz', 'unidecode', 'emoji', 'elasticsearch', 'celery==4.1.1', 'python-dateutil', 'pyyaml'],
)
