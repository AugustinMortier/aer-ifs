from datetime import datetime, timedelta
from pathlib import Path

import xarray as xr


def read_od(path: Path, filename: str, datetime: datetime) -> xr.Dataset:
    # the file for dd-mm-yyyy contains forecast for dd+1-mm-yyyy
    datetime = datetime - timedelta(days=1)
    yyyymmdd = datetime.strftime("%Y%m%d")
    vars = [
        "amaod550",
        "bcaod550",
        "duaod550",
        "niaod550",
        "omaod550",
        "ssaod550",
        "suaod550",
        "aod550",
    ]
    ifs_file = Path(path, filename.replace("YYYYMMDD", yyyymmdd))
    # select first time index: 00:00:00Z
    ds = xr.open_dataset(ifs_file)[vars].isel(time=0).load()
    return ds


def read_rh(datetime: datetime, CFG: dict) -> xr.Dataset:
    # first try the metproduction file
    try:
        print(
            f"Trying to read the metproduction file for {datetime.strftime('%Y%m%d')}"
        )
        path = CFG.get("paths").get("ifs_rh_metproduction")
        filename = CFG.get("filenames").get("ifs_rh_metproduction")
        # the file for dd-mm-yyyy contains forecast for dd+1-mm-yyyy
        datetime_file = datetime - timedelta(days=1)
        yyyymmdd = datetime_file.strftime("%Y%m%d")
        yyyy = datetime_file.strftime("%Y")
        vars = ["relative_humidity_pl"]
        ifs_file = Path(path, yyyy, filename.replace("YYYYMMDD", yyyymmdd))
        # select third time index: 00:00:00Z (the two first being 18, 21)
        ds = xr.open_dataset(ifs_file)[vars].isel(time=2).load()
        # convert longitude from -180 180 to 0 360
        ds = ds.assign_coords(longitude=((ds.longitude + 360) % 360))
        # sort longitude
        ds = ds.sortby("longitude")
        # extract value at the last pressure level (close to the ground)
        ds = ds.isel(pressure=len(ds.pressure) - 1).drop_vars(["time", "pressure"])
    except FileNotFoundError:
        print(f"File {ifs_file} not found. Trying to read the archive file instead.")
        path = CFG.get("paths").get("ifs_rh_archive")
        filename = CFG.get("filenames").get("ifs_rh_archive")
        # the file for dd-mm-yyyy contains forecast for dd-mm-yyyy: CHECK THAT
        datetime_file = datetime
        yyyymmdd = datetime_file.strftime("%Y%m%d")
        yyyy = datetime_file.strftime("%Y")
        vars = ["r"]
        ifs_file = Path(path, yyyy, filename.replace("YYYYMMDD", yyyymmdd))
        # select first time index: 00:00:00Z: CHECK THAT
        ds = xr.open_dataset(ifs_file)[vars].isel(time=0).load()
        # the longitude is already given in 0 360
        # drop time dimension
        ds = ds.drop_vars(["time"]).rename({"r": "relative_humidity_pl"})
    return ds


def get_aer_properties() -> xr.Dataset:
    path = Path(Path(__file__).parent, "..", "config", "aerosol_ifs_49R1_20230725.nc")
    ds = xr.open_dataset(path)
    return ds
