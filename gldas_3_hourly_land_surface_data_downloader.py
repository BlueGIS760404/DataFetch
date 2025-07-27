"""
✅ Use .netrc Authentication (Secure + Supported)
🔐 Step 1: Create .netrc File
Create a file called .netrc in your home directory (e.g. C:\Users\YourName\.netrc on Windows or ~/.netrc on Linux/macOS) with the following contents:

machine urs.earthdata.nasa.gov
login _________
password _________

Then make sure its permissions are secure:

On Linux/macOS:
chmod 600 ~/.netrc

🔐 Step 2: Modify Script to Use .netrc (no credentials in code)
session.auth = None  # Use .netrc 
"""

import os
import requests
from datetime import datetime, timedelta
from tqdm import tqdm

# Save directory
SAVE_DIR = 'gldas_raw'
os.makedirs(SAVE_DIR, exist_ok=True)

# Setup session with Earthdata .netrc authentication
session = requests.Session()
session.auth = None  # Use credentials from ~/.netrc
session.headers.update({'User-Agent': 'python-requests/2.25.1'})

# Base URL for GLDAS
BASE_URL = 'https://data.gesdisc.earthdata.nasa.gov/data/GLDAS/GLDAS_NOAH025_3H.2.1'

# Generate 3-hour timestamps for 2024
start = datetime(2024, 1, 1, 0)
end = datetime(2025, 1, 1, 0)
delta = timedelta(hours=3)
timestamps = []
while start < end:
    timestamps.append(start)
    start += delta

# Download loop
for dt in tqdm(timestamps, desc="Downloading GLDAS"):
    yyyy = dt.strftime('%Y')
    doy = dt.strftime('%j')
    yyyymmdd = dt.strftime('%Y%m%d')
    hhmm = dt.strftime('%H%M')
    filename = f'GLDAS_NOAH025_3H.A{yyyymmdd}.{hhmm}.021.nc4'
    url = f'{BASE_URL}/{yyyy}/{doy}/{filename}'
    out_path = os.path.join(SAVE_DIR, filename)

    if os.path.exists(out_path):
        continue

    response = session.get(url, stream=True)
    if response.status_code == 200:
        with open(out_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        print(f"Failed to download {filename} — HTTP {response.status_code}")


##############################################################################################################################################################
##############################################################################################################################################################
##############################################################################################################################################################


# Use this one in case you encounter any interruption in the process of above code!

import os
import requests
import logging
from datetime import datetime, timedelta
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_3H.2.1"
SAVE_DIR = "gldas_raw"
USERNAME = "rezagisrs1368"  # Replace with your Earthdata username
PASSWORD = "Rezagisrs1368!"  # Replace with your Earthdata password
DELAY = 0.5  # Reduced delay between downloads (in seconds)
MAX_WORKERS = 3  # Number of concurrent download threads

# Create directory if it doesn't exist
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# Function to download a file with authentication
def download_file(url, out_path):
    try:
        with requests.Session() as session:
            session.auth = (USERNAME, PASSWORD)
            with session.get(url, stream=True) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                with open(out_path, 'wb') as f, tqdm(
                    desc=out_path.split('/')[-1],
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024
                ) as bar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for {url}: {e}")
        raise
    except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
        logger.error(f"Connection error for {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}")
        raise

# Function to download a single timestamp
def download_timestamp(dt):
    yyyy = dt.strftime('%Y')
    doy = dt.strftime('%j')
    yyyymmdd = dt.strftime('%Y%m%d')
    hhmm = dt.strftime('%H%M')
    filename = f'GLDAS_NOAH025_3H.A{yyyymmdd}.{hhmm}.021.nc4'
    url = f'{BASE_URL}/{yyyy}/{doy}/{filename}'
    out_path = os.path.join(SAVE_DIR, filename)
    
    if os.path.exists(out_path):
        logger.info(f"Skipping {filename} (already exists)")
        return True  # Return True to indicate skip (no download needed)
    
    try:
        logger.info(f"Downloading {filename}")
        download_file(url, out_path)
        logger.info(f"Successfully downloaded {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {filename}: {e}")
        return False
    finally:
        time.sleep(DELAY)  # Delay to avoid overwhelming the server

# Generate timestamps
start = datetime(2024, 1, 1, 0)
end = datetime(2025, 1, 1, 0)
timestamps = [start + timedelta(hours=3*x) for x in range(int((end - start).total_seconds() / 3600 / 3))]

# Download files in parallel
logger.info(f"Starting download of {len(timestamps)} files")
downloaded = 0
skipped = 0
failed = 0

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    results = list(tqdm(
        executor.map(download_timestamp, timestamps),
        total=len(timestamps),
        desc="Processing GLDAS timestamps"
    ))

# Summarize results
for result, dt in zip(results, timestamps):
    filename = f"GLDAS_NOAH025_3H.A{dt.strftime('%Y%m%d')}.{dt.strftime('%H%M')}.021.nc4"
    if result:
        if os.path.exists(os.path.join(SAVE_DIR, filename)):
            skipped += 1
        else:
            downloaded += 1
    else:
        failed += 1

logger.info(f"Summary: Downloaded {downloaded}, Skipped {skipped}, Failed {failed}")
