from datetime import datetime
from pathlib import Path
from rich.progress import track

import xarray as xr

def read(path: Path, datetime: datetime, verbose) -> dict:
    dict = {}
    # list all files in the directory
    files = [f for f in Path(path, datetime.strftime('%Y'), datetime.strftime('%m'), datetime.strftime('%d')).iterdir() if f.is_file()]
    vars = []
    for file in track(files, description=f':book: Read v-profiles data', disable=not verbose):
        ds = xr.open_dataset(file, chunks=-1)[vars].load()
        station_id = f"{ds.attrs['wigos_station_id']}-{ds.attrs['instrument_id']}"
        dict[station_id] = ds.attrs
    
    return dict