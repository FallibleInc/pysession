from setuptools import setup
import os
from os.path import exists, expanduser
from shutil import copyfile

ROOT = os.path.abspath(os.path.dirname(__file__))

if not os.path.exists(expanduser('~') + '/.pysession'):
    os.makedirs(expanduser('~') + '/.pysession')

copyfile(ROOT + '/pysession.py', expanduser('~') + '/.pysession/pysession.py')


setup(
    name='pysession',
    version='0.2',
    description='Automatically save python interpreter session code to a file or secret Gist',
    author='Fallible',
    author_email='hello@fallible.co',
    url='https://github.com/FallibleInc/pysession',
    download_url='https://github.com/FallibleInc/pysession/tarball/0.2',
    py_modules=['pysession'],
    install_requires=[],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: IPython",
        "Framework :: IDLE",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Utilities",
    ],
)
