from datetime import datetime, timedelta
from pathlib import Path

import xarray as xr


def final_path(datetime: datetime, root: str, filename: str) -> Path:
    yyyymmdd = datetime.strftime("%Y%m%d")
    yyyy = datetime.strftime("%Y")
    return Path(root, yyyy, filename.replace("YYYYMMDD", yyyymmdd))


def read_od(datetime: datetime, CFG: dict) -> xr.Dataset:
    root = CFG.get("paths").get("ifs_od")
    filename00 = CFG.get("filenames").get("ifs_od_00UTC")
    filename12 = CFG.get("filenames").get("ifs_od_12UTC")
    ifs_file = final_path(datetime, root, filename00)
    if not ifs_file.exists():
        ifs_file = final_path(datetime - timedelta(days=1), root, filename12)

    print(f"using ifs file {ifs_file}")
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
    # daily average and date selection
    ds = (
        xr.open_dataset(ifs_file)[vars]
        .resample(time="D")
        .mean()
        .sel(time=datetime)
        .load()
    )
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
        ifs_file = Path(path, filename.replace("YYYYMMDD", yyyymmdd))
        # daily average and date selection
        ds = (
            xr.open_dataset(ifs_file)[vars]
            .resample(time="D")
            .mean()
            .sel(time=datetime)
            .load()
        )
        # convert longitude from -180 180 to 0 360
        ds = ds.assign_coords(longitude=((ds.longitude + 360) % 360))
        # sort longitude
        ds = ds.sortby("longitude")
        # extract value at the last pressure level (close to the ground)
        ds = ds.isel(pressure=len(ds.pressure) - 1).drop_vars(["time", "pressure"])
    except (Exception, FileNotFoundError) as e:
        print(
            f"Could not use the metproduction file ({e}). Trying to read the archive file instead."
        )
        root = CFG.get("paths").get("ifs_rh_archive")
        filename00 = CFG.get("filenames").get("ifs_rh_archive_00UTC")
        filename12 = CFG.get("filenames").get("ifs_rh_archive_12UTC")
        ifsrh_file = final_path(datetime, root, filename00)
        if not ifsrh_file.exists():
            ifsrh_file = final_path(datetime - timedelta(days=1), root, filename12)
        print(f"Using ifs file {ifsrh_file}")
        vars = ["r"]
        # daily average and date selection
        ds = (
            xr.open_dataset(ifsrh_file)[vars]
            .resample(time="D")
            .mean()
            .sel(time=datetime)
            .load()
        )
        # the longitude is already given in 0 360
        # drop time dimension
        ds = ds.drop_vars(["time"]).rename({"r": "relative_humidity_pl"})
    return ds


def get_aer_properties() -> xr.Dataset:
    path = Path(Path(__file__).parent, "..", "config", "aerosol_ifs_49R1_20230725.nc")
    ds = xr.open_dataset(path)
    return ds
