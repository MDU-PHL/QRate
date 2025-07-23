#!/usr/bin/env python3

import argparse
import os
import sys
import yaml
import pkg_resources
from datetime import datetime
from .csv_handler import read_csv, write_csv
from .curation_engine import CurationEngine
from .species_checker import SpeciesChecker
from . import __version__

def log_with_timestamp(message, file=None):
    """Print message with timestamp prefix."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    print(formatted_message, file=file)

def find_config_file(config_name):
    """Find configuration file, trying package resources first, then relative paths."""
    try:
        # Try to get from package resources first
        return pkg_resources.resource_filename('qrate', f'config/{config_name}')
    except:
        # Fallback to relative paths
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'config', config_name),
            os.path.join('config', config_name),
            config_name
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError(f"Configuration file '{config_name}' not found")

def main():
    parser = argparse.ArgumentParser(description="QRate - QC data curation tool for bacterial genomics")
    parser.add_argument("input_file", nargs='?', help="Path to input CSV file")
    parser.add_argument("-o", "--output", help="Path to output CSV file (default: input file with .curated suffix)")
    default_rules_path = find_config_file('rules.yaml')
    parser.add_argument(
        "-r", "--rules",
        help=f"Path to rules YAML file (default: {default_rules_path})"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-c","--check-species", action="store_true", help="Check species counts and provide file expectations after limisfy QC step")
    parser.add_argument("--version", action="version", version=f"QRate {__version__}")
    
    args = parser.parse_args()
    
    # Check if input file is provided (required unless --version is used)
    if not args.input_file:
        parser.error("the following arguments are required: input_file")
    
    # Set default output file if not provided
    if not args.output:
        base, ext = os.path.splitext(args.input_file)
        args.output = f"{base}.curated{ext}"
    
    # Find rules configuration file
    rules_file = args.rules
    if not rules_file:
        try:
            rules_file = find_config_file('rules.yaml')
        except FileNotFoundError:
            log_with_timestamp("Error: No rules file specified and default 'rules.yaml' not found", file=sys.stderr)
            log_with_timestamp("Please specify a rules file with -r/--rules or ensure 'rules.yaml' exists", file=sys.stderr)
            return 1
    
    # Load rules configuration
    try:
        with open(rules_file, 'r') as f:
            rules = yaml.safe_load(f)
        if not args.verbose:
            log_with_timestamp(f"Loading rules from: {rules_file}")
    except FileNotFoundError as e:
        log_with_timestamp(f"Error: Configuration file not found - {e}", file=sys.stderr)
        return 1
    except yaml.YAMLError as e:
        log_with_timestamp(f"Error parsing YAML configuration: {e}", file=sys.stderr)
        return 1
    
    # Process QC data
    try:
        if not args.verbose:
            log_with_timestamp(f"Reading input file: {args.input_file}")
        
        qc_data = read_csv(args.input_file)
        
        if not args.verbose:
            log_with_timestamp(f"Processing {len(qc_data)} records...")
        
        # Initialize curation engine
        curation_engine = CurationEngine(rules, verbose=args.verbose)
        
        # Apply curation logic
        processed_data = curation_engine.curate_data(qc_data)
        
        write_csv(processed_data, args.output)
        
        if not args.verbose:
            log_with_timestamp(f"Output written to: {args.output}")
            log_with_timestamp("Processing completed successfully!")
        elif args.verbose:
            log_with_timestamp(f"\nSUMMARY:")
            log_with_timestamp(f"Processed {len(qc_data)} records")
            log_with_timestamp(f"Output written to {args.output}")
        
        # Run species checking if requested
        if args.check_species:
            if not args.verbose:
                log_with_timestamp(f"\n{'='*50}")
                print("SPECIES ANALYSIS")
                print(f"{'='*50}")
            
            species_checker = SpeciesChecker()
            species_success = species_checker.check_species(args.input_file, verbose=args.verbose)
            
            if not species_success:
                log_with_timestamp("Warning: Species checking encountered errors", file=sys.stderr)
    
    except FileNotFoundError as e:
        log_with_timestamp(f"Error: Input file not found - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        log_with_timestamp(f"Error processing QC data: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
