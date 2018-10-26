"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='feeder-utilities',

    version='1.0.1',

    description='Module for feeder utilities, both client and server, handling health and integrity checking',
    long_description=long_description,

    url='https://github.com/LandRegistry',

    author='James Lademann',
    author_email='james.lademann@landregistry.gov.uk',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4'
    ],

    keywords='development',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    install_requires=['kombu==3.0.35', ''],

    test_suite='nose.collector',
    tests_require=['nose', 'coverage'],

    entry_points={
        'console_scripts': ['feeder-rpc-client=feeder_utilities.feeder_rpc_client:main']
    }
)
