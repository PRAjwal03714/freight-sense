"""
Downloads supply chain dataset from Kaggle.

What this dataset has:
- 180,000+ orders with actual vs scheduled delivery dates
- Routes (origin city → destination city)
- Shipping modes (air, sea, road)
- Delay days calculated from the difference

Why this dataset:
- Real historical data (2015-2018)
- Has the exact features we need (routes + delays)
- Free and public
"""
import os
from kaggle.api.kaggle_api_extended import KaggleApi

def download_supply_chain_data():
    api = KaggleApi()
    api.authenticate()
    
    # DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS
    dataset = "shashwatwork/dataco-smart-supply-chain-for-big-data-analysis"
    
    download_path = "data/kaggle"
    os.makedirs(download_path, exist_ok=True)
    
    print(f"📥 Downloading {dataset}...")
    api.dataset_download_files(dataset, path=download_path, unzip=True)
    print(f"✅ Downloaded to {download_path}/")
    
    # List what we got
    files = os.listdir(download_path)
    print(f"📂 Files: {files}")

if __name__ == "__main__":
    download_supply_chain_data()