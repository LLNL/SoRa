"""
Setup file for SoRa
"""

from setuptools import setup

setup(name='sora',
      version='1.0.0',
      packages=['sora'],
      description='A DEAP based Symbolic Regression tool',
      long_description = open("README.rst").read(),
      license='BSD',
      url='none',
      maintainer='Jim Leek',
      maintainer_email='leek2@llnl.gov',
      install_requires=['deap>=1.1.0', 'numpy>=1.9.2', 'mpi4py'],
      extras_require = { 'prettyprint' : ['sympy>=0.7.6'] },
      entry_points = {
        'console_scripts': [
            'sora = sora.sora:main',
            'modifydata = sora.modifydata.main',
            ]
        }
      )
