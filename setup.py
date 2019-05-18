# -*- coding: utf-8 -*-

import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open("botshot/version.py") as fp:
    version_dict = {}
    exec(fp.read(), version_dict)
    __version__ = version_dict['__version__']

setup(
    name='botshot',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    license='GPL',
    description='A framework for creating stateful chatbots on Django.',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/prihoda/botshot',
    author='David Příhoda, Matúš Žilinec, Jakub Drdák',
    author_email='david.prihoda@gmail.com, zilinec.m@gmail.com',
    entry_points={
          'console_scripts': [
              'bots = botshot.bots:main'
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
        # 'Programming Language :: Python :: 3.7',  Not compatible yet, waiting for Celery 4.3 !
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Communications :: Chat',
    ],
    install_requires=['django>=2.1.5', 'networkx', 'requests', 'six', 'sqlparse', 'wit==4.3.0', 'wheel', 'redis', 'Pillow', 'jsonfield',
                      'pytz', 'unidecode', 'emoji', 'elasticsearch', 'celery>=4.1.1', 'python-dateutil', 'pyyaml', 'djangorestframework',
                      'pytest', 'pytest-django', 'mock'],
)
