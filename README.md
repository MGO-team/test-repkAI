# REPKAI - REtrieve Patent (K)Constants from pharmaceutical patents with AI-agents

## Introduction

The pharmaceutical and biotech industries generate vast amounts of valuable bioactivity data that remains locked within patent documents. Binding affinity measurements such as *Ki*, *Kd*, *IC50*, *EC50* represent fundamental pharmacological parameters that quantify molecular interactions between drug candidates and their biological targets. While commercial databases like Reaxys and GOSTAR provide structured access to some of this information, their proprietary nature and high costs create significant barriers for academic researchers. This project develops an AI-powered pipeline to extract structured bioactivity data from chemical patents, creating an open-access alternative.

## Patent Acquisition and Preprocessing

**Data Sources:**

- Bulk PDF downloads from Google Patents using SureChEMBL-derived patent IDs
- Supplementary information on target proteins was obtained from the NCBI Protein Database using automated API queries and manual curation

**Principe of procecessing**

The system operates in two sequential major stages: <ins>pre-annotation</ins> and <ins>data extraction</ins> from pre-annotated data.
 
 <ins>Pre-annotation</ins>:
1) First, it retrieves patent documents through API calls to databases, performing initial processing to structure the raw data. 
2) Then each document is spitted into overlapping chunks of a given size and degree of overlapping. 
3) Then each such chunk is pre-annotated.  For annotation LLM is used with a prompt that roughly estimates if there any data of interest in the given chunk. 
3) After that data chunks that were annotated as "potentially containing" data on protein binding constants these chunks are passed down to the AI agent. 

<ins>Data extraction</ins>:
1) AI agent is promted to extract data of interest like constants, compound names and protein names
    - "Ki (nM)"
    - "IC50 (nM)"
    - "Kd (nM)"
    - "EC50 (nM)"
    - "assay"
    - "ligand_name"
    - "ligand_SMILES"
    - "protein_name"
    - "protein_FASTA"

2) AI agent can also use two available tools: fucntion to convert ligand name to smiles structure and function to retrieve fasta sequence by protein name.
3) Resulted data is extracted in json format


## Requirements

To install all required packages:
- for `conda`

Run `conda env create -f min_test_conda_requirements.yml`. This will create a new env called `patent_parser` in your default env location. To activate env run `conda activate patent_parser`

## Usage

1) Go to `patent_parser/config.py` file and edit settings to correct. Then just run main execution script with `python patent_parser/run_parser.py`
2) Edit `.env_example` file according to your data and rename it to `.env`

## Downloads

Download options can be set up via config file. Please note, that databases require quite a lot of disk space: SureChEMBL (16 Gb) and ChEMBL (9 Gb)
