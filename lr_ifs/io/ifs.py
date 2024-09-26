from datetime import datetime, timedelta
from pathlib import Path

import xarray as xr

def read(path: Path, datetime: datetime):
    # the file for dd-mm-yyyy contains forecast for dd+1-mm-yyyy
    datetime = datetime - timedelta(days=1)
    yyyymmdd = datetime.strftime('%Y%m%d')
    vars = ["amaod550", "bcaod550", "duaod550", "niaod550", "omaod550", "ssaod550", "suaod550", "aod550"]
    ifs_file = Path(path, f'{yyyymmdd}_cIFS-12UTC_o-suite_surface.nc')
    ds = xr.open_dataset(ifs_file)[vars].isel(time=0).load()
    return ds