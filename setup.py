#!/usr/bin/python
import os
import sys
import uuid
from setuptools import setup, find_packages


requirements_path = os.path.join(
    os.path.dirname(__file__),
    'requirements.txt',
)
try:
    from pip.req import parse_requirements
    requirements = [
        str(req.req) for req in parse_requirements(
            requirements_path,
            session=uuid.uuid1()
        )
    ]
except ImportError:
    requirements = []
    with open(requirements_path, 'r') as in_:
        requirements = [
            req for req in in_.readlines()
            if not req.startswith('-')
            and not req.startswith('#')
        ]

# Python 2.6 does not come with importlib pre-installed
if sys.version_info < (2, 7):
    requirements.append('importlib>=1.0.1')


setup(
    name="slack-pdb",
    version="2.0.3",
    description=(
        "Collaboratively debug your Python application in Slack"
    ),
    author="Adam Coddington",
    author_email="me@adamcoddington.net",
    url="http://github.com/coddingtonbear/slack-pdb",
    packages=find_packages(),
    install_requires=requirements,
    tests_require=['tox', 'pytest', 'mock'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Topic :: Software Development :: Debuggers",
    ]
)
