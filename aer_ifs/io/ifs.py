from datetime import datetime, timedelta
from pathlib import Path

import xarray as xr

def read_od(path: Path, datetime: datetime) -> xr.Dataset:
    # the file for dd-mm-yyyy contains forecast for dd+1-mm-yyyy
    datetime = datetime - timedelta(days=1)
    yyyymmdd = datetime.strftime('%Y%m%d')
    vars = ["amaod550", "bcaod550", "duaod550", "niaod550", "omaod550", "ssaod550", "suaod550", "aod550"]
    ifs_file = Path(path, f'{yyyymmdd}_cIFS-12UTC_o-suite_surface.nc')
    # select first time index: 00:00:00Z
    ds = xr.open_dataset(ifs_file)[vars].isel(time=0).load()
    return ds

def read_rh(path: Path, datetime: datetime) -> xr.Dataset:
    # the file for dd-mm-yyyy contains forecast for dd+1-mm-yyyy
    datetime = datetime - timedelta(days=1)
    yyyymmdd = datetime.strftime('%Y%m%d')
    vars = ["relative_humidity_pl"]
    ifs_file = Path(path, f'ec_atmo_0_1deg_{yyyymmdd}T180000Z_pl.nc')
    # select third time index: 00:00:00Z (the two first being 18, 21)
    ds = xr.open_dataset(ifs_file)[vars].isel(time=2).load()
    # convert longitude from -180 180 to 0 360
    ds = ds.assign_coords(
        longitude=((ds.longitude + 360) % 360)
    )
    # sort longitude
    ds = ds.sortby('longitude')
    # extract value at the last pressure level (close to the ground)
    ds = ds.isel(pressure=len(ds.pressure)-1).drop_vars(['time', 'pressure'])
    return ds

def get_aer_properties() -> xr.Dataset:
    path = Path(Path(__file__).parent,'..','config','aerosol_ifs_49R1_20230725.nc')
    ds = xr.open_dataset(path)
    return ds