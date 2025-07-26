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
