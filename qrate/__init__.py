"""
QRate - A QC data curation tool for bacterial genomics

QRate is a command-line tool for curating bacterial QC data based on 
configurable rules. It provides a flexible framework for applying 
quality control standards to genomic data.
"""

__version__ = "0.1.0"
__author__ = "Himal Shrestha"
__email__ = "himal.shrestha@unimelb.edu.au"

from .curation_engine import CurationEngine
from .csv_handler import read_csv, write_csv

__all__ = ["CurationEngine", "read_csv", "write_csv"]
