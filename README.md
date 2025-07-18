# QCheck
This repo contains scripts to process `standard_bacteria_qc.csv` file obtained from the `mdudatagen` pipeline.

## Features
- Reads QC results from CSV files.
- Applies customisable curation rules defined in YAML configuration files.
- Generates updated QC results with appropriate comments based on defined logic.

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/MDU-PHL/QCheck.git
   cd QCheck
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the QC Curation Tool, use the following command:

```sh
python src/main.py --input <path_to_input_csv> --output <path_to_output_csv> --rules config/rules.yaml
```

### Command-Line Arguments
- `--input`: Path to the input CSV file containing QC results.
- `--output`: Path where the updated QC results will be saved.
- `--rules`: rules configuration file (default: `config/rules.yaml`).

## Configuration
The curation rules and mappings are defined in the YAML files located in the `config` directory. You can modify these files to adjust the curation logic as needed.

## Example
An example input CSV file might look like this:
```
SPECIES_EXP,SPECIES_OBS,TEST_COVERAGE,COVERAGE,TEST_GENOME_SIZE_KMER,GENOME_SIZE_KMER,TEST_QC,COMMENT

```

After processing, the output CSV will reflect the applied curation logic based on the defined rules.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

