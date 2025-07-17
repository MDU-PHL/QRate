#!/usr/bin/env python3
# filepath: /home/unimelb.edu.au/himals/onedrive-unimelb/1_projects/pipelines/QCheck/src/main.py

import argparse
import os
import sys
import yaml
import csv
from csv_handler import read_csv, write_csv
from curation_engine import CurationEngine

def main():
    parser = argparse.ArgumentParser(description="QC Validator - Curate QC data based on configurable rules")
    parser.add_argument("input_file", help="Path to input CSV file")
    parser.add_argument("-o", "--output", help="Path to output CSV file (default: input file with .curated suffix)")
    parser.add_argument("-r", "--rules", help="Path to rules YAML file", default="config/rules.yaml")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Set default output file if not provided
    if not args.output:
        base, ext = os.path.splitext(args.input_file)
        args.output = f"{base}.curated{ext}"
    
    # Load rules configuration only
    try:
        with open(args.rules, 'r') as f:
            rules = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"Error: Configuration file not found - {e}", file=sys.stderr)
        return 1
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}", file=sys.stderr)
        return 1
    
    # Process QC data
    try:
        qc_data = read_csv(args.input_file)
        
        # Initialize curation engine
        curation_engine = CurationEngine(rules, verbose=args.verbose)
        
        # Apply curation logic
        processed_data = curation_engine.curate_data(qc_data)
        
        write_csv(processed_data, args.output)
        
        if args.verbose:
            print(f"Processed {len(qc_data)} records")
            print(f"Output written to {args.output}")
    
    except Exception as e:
        print(f"Error processing QC data: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())