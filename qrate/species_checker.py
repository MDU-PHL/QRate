#!/usr/bin/env python3

import csv
import sys
from datetime import datetime

def log_with_timestamp(message, file=None):
    """Print message with timestamp prefix."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    print(formatted_message, file=file)

class SpeciesChecker:
    """Species checker for QC CSV files."""
    
    def __init__(self):
        self.species_list = [
            "Salmonella", "Listeria monocytogenes", "Escherichia coli",
            "Streptococcus pneumoniae", "Streptococcus pyogenes", 
            "Neisseria meningitidis", "Legionella pneumophila", 
            "Neisseria gonorrhoeae", "Mycobacterium tuberculosis",
            "Haemophilus influenzae"
        ]
    
    def count_species_in_file(self, file_path):
        """Count occurrences of each species in the CSV file."""
        species_count = {species: 0 for species in self.species_list}
        
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)  # Skip the header row
                for row in reader:
                    for species in self.species_list:
                        if any(species in cell for cell in row):
                            species_count[species] += 1
        except FileNotFoundError:
            log_with_timestamp(f"Error: File '{file_path}' not found", file=sys.stderr)
            return None
        except Exception as e:
            log_with_timestamp(f"Error reading file '{file_path}': {e}", file=sys.stderr)
            return None

        return species_count

    def count_no_identification(self, file_path):
        """Count samples with 'no identification'."""
        no_identification_count = 0
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)  # Skip the header row
                for row in reader:
                    if any("no identification" in cell.lower() for cell in row):
                        no_identification_count += 1
        except FileNotFoundError:
            log_with_timestamp(f"Error: File '{file_path}' not found", file=sys.stderr)
            return None
        except Exception as e:
            log_with_timestamp(f"Error reading file '{file_path}': {e}", file=sys.stderr)
            return None
        
        return no_identification_count

    def print_species_recommendations(self, species_count):
        """Print recommendations for each detected species."""
        print("\n---\nExpected files:")
        print("* QC file")
        print("* 2 NTC files")
        print("* 1 Sequence report file")
        print("* 1 Speciation file")
        print("* MMS118 (AMR)")

        for species in self.species_list:
            if species_count[species] > 0:
                if species == "Salmonella":
                    print("Check for sistr typing file, MMS184 (Salmonella AMR), and MMS181 (Salmonella cgMLST)")
                elif species == "Listeria monocytogenes":
                    print("Check for lissero typing file")
                elif species == "Escherichia coli":
                    print("Check for EcOH typing file")
                elif species == "Streptococcus pneumoniae":
                    print("Check for seroba typing file")
                elif species == "Streptococcus pyogenes":
                    print("Check for emmtyper typing file")
                elif species == "Neisseria meningitidis":
                    print("Check for meningotyper typing file")
                elif species == "Legionella pneumophila":
                    print("Check for MMS123LpSBT typing file")
                elif species == "Neisseria gonorrhoeae":
                    print("Check for MMS181 (Neisseria gonorrhoeae cgMLST) and ngmaster typing file")
                elif species == "Mycobacterium tuberculosis":
                    print("Check for MMS155 (M. tuberculosis AMR)")
                elif species == "Haemophilus influenzae":
                    print("Check for BIS009 hicap typing file")

    def check_species(self, file_path, verbose=False):
        """Main method to check species in QC file."""
        if verbose:
            print(f"Reading data from file: {file_path}")

        species_count = self.count_species_in_file(file_path)
        if species_count is None:
            return False

        # Print species counts
        for species, count in species_count.items():
            print(f"There are {count} samples for {species}.")

        # Check for "No identification"
        no_identification_count = self.count_no_identification(file_path)
        if no_identification_count is not None:
            print(f"There are {no_identification_count} samples with 'No identification'.")

        # Print recommendations
        self.print_species_recommendations(species_count)
        
        return True
