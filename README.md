# aidac_downloader

AIDAC helps simplifying AI Data collection workflows. AIDAC Downloader is part of AIDAC solution and is used to download dataset from cloud storage.

# Install packages

	pip install -r requirements.txt

# Usage

AIDAC Downloader utility takes the Download Config File (DCF) as input. Please download the DCF from AIDAC dashboard.

To start downloading the dataset run,

	python3 aidac_downloader.py -c downloaded_dcf.json

In case if the project has consent form enabled, aidac_downloader.py utility automatically generates the consent form for every object in PDF format.

