
![Alt text](aidac_logo.png)

# About

Haidata (https://haidata.ai) is an AI Data solutions and services organization catering to the AI data needs of various industries. Started with the objective of contributing to "Data Centric AI", Haidata has invested in all aspects of the AI Data value chain - including services, technology and solutions. As an organization committed to providing jobs for technically qualified youth, who chose to work from rural places rather than cities, Haidata provides affordable AI Data related solutions and services to organizations across the world from the villages of Nilgiris hills, in India.

# AIDAC Downloader

AIDAC is an AI Data collection platform and helps in streamlining AI data collection workflows. AIDAC Downloader is part of the AIDAC solution and is used to download dataset from cloud storage. AIDAC Downloader utility is usually used at the end of the data collection process to download the approved datasets (after QC).

# Install packages

	pip install -r requirements.txt

# Usage

AIDAC Downloader utility takes the Download Config File (DCF) as input. Please download the DCF from AIDAC dashboard.

To start downloading the dataset run,

	python3 aidac_downloader.py -c downloaded_dcf.json

In case if the project has consent form enabled, aidac_downloader.py utility automatically generates the consent form for every object in PDF format.

# Customer Support

Please write to aidac-support@haidata.ai 



