## Requirements

To install all required packages:
- for `conda`

Run `conda env create -f min_test_conda_requirements.yml`. This will create a new env called `patent_parser` in your default env location. To activate env run `conda activate patent_parser`

## Usage

Go to `patent_parser/config.py` file and edit settings to correct. Then just run main execution script with `python patent_parser/run_parser.py`

## Downloads

Download options can be set up via config file. Please note, that databases require quite a lot of disk space: SureChEMBL (16 Gb) and ChEMBL (9 Gb)