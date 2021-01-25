"""This is just for Tox support"""
from setuptools import setup, find_packages

setup(
    name='dbmonitor',
    version='0.1',
    author="Brian Seel",
    author_email="brian.seel@baltimorecity.gov",
    description="Notifies when a database stops getting expected updates",
    packages=find_packages('src'),
    package_data={'dbmonitor': ['py.typed'], },
    python_requires='>=3.0',
    package_dir={'': 'src'},
    install_requires=[
        'sqlalchemy',
    ]
)
