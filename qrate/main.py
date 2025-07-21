#!/usr/bin/env python3

import argparse
import os
import sys
import yaml
import csv
import pkg_resources
from .csv_handler import read_csv, write_csv
from .curation_engine import CurationEngine

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
    parser.add_argument("input_file", help="Path to input CSV file")
    parser.add_argument("-o", "--output", help="Path to output CSV file (default: input file with .curated suffix)")
    parser.add_argument("-r", "--rules", help="Path to rules YAML file", default=None)
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
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
            print("Error: No rules file specified and default 'rules.yaml' not found", file=sys.stderr)
            print("Please specify a rules file with -r/--rules or ensure 'rules.yaml' exists", file=sys.stderr)
            return 1
    
    # Load rules configuration
    try:
        with open(rules_file, 'r') as f:
            rules = yaml.safe_load(f)
        if not args.verbose:
            print(f"Loading rules from: {rules_file}")
    except FileNotFoundError as e:
        print(f"Error: Configuration file not found - {e}", file=sys.stderr)
        return 1
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}", file=sys.stderr)
        return 1
    
    # Process QC data
    try:
        if not args.verbose:
            print(f"Reading input file: {args.input_file}")
        
        qc_data = read_csv(args.input_file)
        
        if not args.verbose:
            print(f"Processing {len(qc_data)} records...")
        
        # Initialize curation engine
        curation_engine = CurationEngine(rules, verbose=args.verbose)
        
        # Apply curation logic
        processed_data = curation_engine.curate_data(qc_data)
        
        write_csv(processed_data, args.output)
        
        if not args.verbose:
            print(f"Output written to: {args.output}")
            print("Processing completed successfully!")
        elif args.verbose:
            print(f"\nSUMMARY:")
            print(f"Processed {len(qc_data)} records")
            print(f"Output written to {args.output}")
    
    except FileNotFoundError as e:
        print(f"Error: Input file not found - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error processing QC data: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
