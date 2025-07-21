# QRate (QCheck)

QRate is a command-line tool for curating bacterial QC data based on configurable rules. It processes `standard_bacteria_qc.csv` files obtained from the `mdudatagen` pipeline and provides a flexible framework for applying quality control standards to genomic data.

## Features

- Reads QC results from CSV files
- Applies customizable curation rules defined in YAML configuration files
- Generates updated QC results with appropriate comments based on defined logic
- Command-line interface with `qrate` command
- Configurable rule system with multiple operators
- Species scheme compatibility checking

## Installation

### From Source (Development)

1. Clone the repository:

   ```bash
   git clone https://github.com/MDU-PHL/QCheck.git
   cd QCheck
   ```

2. Install the package in development mode:

   ```bash
   pip install -e .
   ```

### From PyPI (when published)

```bash
pip install qrate
```

## Usage

### Basic Usage

```bash
qrate input_file.csv
```

This will process `input_file.csv` using the default rules and create `input_file.curated.csv`.

### Advanced Usage

```bash
# Specify custom output file
qrate input_file.csv -o output_file.csv

# Use custom rules file
qrate input_file.csv -r custom_rules.yaml

# Enable verbose output for detailed logging
qrate input_file.csv -v

# Combine options
qrate input_file.csv -o output.csv -r custom_rules.yaml -v
```

### Command-Line Arguments

- `input_file`: Path to the input CSV file containing QC results (required)
- `-o, --output`: Path where the updated QC results will be saved (default: input file with .curated suffix)
- `-r, --rules`: Path to rules configuration file (default: built-in rules.yaml)
- `-v, --verbose`: Enable verbose output for detailed rule evaluation logging

## Configuration

The curation rules and mappings are defined in YAML files. The package includes default configuration files, but you can specify custom rules using the `-r/--rules` option.

### Rule Structure

```yaml
- id: "RULE_ID"
  description: "Description of what this rule does"
  conditions:
    - field: FIELD_NAME
      operator: "=="
      value: "expected_value"
  actions:
    - field: MMS103
      value: "FAIL"
    - field: COMMENT
      value: "Reason for failure"
```

### Supported Operators

- `==`, `!=`: Equality/inequality
- `<`, `<=`, `>`, `>=`: Numeric comparisons
- `contains`: String contains (case-insensitive)
- `between_pct`: Percentage-based range checking
- `species_scheme_compatible`: Check species-scheme compatibility
- `genus_level_match`: Check genus-level matching
- `species_subspecies_match`: Check subspecies matching

## Example

An example input CSV file might look like this:

```csv
ISOLATE,SPECIES_EXP,SPECIES_OBS,TEST_COVERAGE,COVERAGE,TEST_GENOME_SIZE_KMER,GENOME_SIZE_KMER,MMS103,MMS109,TEST_QC,COMMENT
sample1,Salmonella enterica,Salmonella enterica,true,45.2,true,4800000,PASS,PASS,PASS,
```

After processing with `qrate`, the output will reflect the applied curation logic based on the defined rules.

## Development

### Project Structure

```
QCheck/
├── qrate/                  # Main package
│   ├── __init__.py
│   ├── main.py            # CLI entry point
│   ├── curation_engine.py # Core curation logic
│   ├── csv_handler.py     # CSV I/O functions
│   ├── operators.py       # Rule evaluation operators
│   └── config/            # Configuration files
│       ├── rules.yaml
│       └── species_scheme_mapping.yaml
├── setup.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Adding New Rules

1. Open the `rules.yaml` file (or create a custom one)
2. Add your new rule following the existing format
3. Test with sample data
4. Document the rule behavior

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
