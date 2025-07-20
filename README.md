## Requirements

To install all required packages:
- for `conda`

Run `conda env create -f min_test_conda_requirements.yml`. This will create a new env called `patent_parser` in your default env location. To activate env run `conda activate patent_parser`

## Preprocessing

To download sureChEMBL go to `001_preprocessing/001_download_surechembl.py` and change path to appropriate. Then run download script with `python 001_preprocessing/001_download_surechembl.py`.