from datetime import datetime
from pathlib import Path
from rich.progress import track

import xarray as xr


def read(path: Path, datetime: datetime, verbose) -> dict:
    dict = {}
    # list all files in the directory
    files = [
        f
        for f in Path(
            path,
            datetime.strftime("%Y"),
            datetime.strftime("%m"),
            datetime.strftime("%d"),
        ).iterdir()
        if f.is_file() and "L2_" in f.name
    ]

    vars = ["station_latitude", "station_longitude", "l0_wavelength"]
    for file in track(
        files, description=f":satellite: Reading L2 e-profile data", disable=not verbose
    ):
        try:
            ds = xr.open_dataset(file, chunks=-1)[vars].load()
        except (OSError, Exception) as e:
            print(f"Error with {file}: {e}")
            continue
        station_id = f"{ds.attrs['wigos_station_id']}-{ds.attrs['instrument_id']}"
        dict[station_id] = ds.attrs
        dict[station_id]["station_latitude"] = ds.station_latitude.data
        dict[station_id]["station_longitude"] = ds.station_longitude.data
        dict[station_id]["l0_wavelength"] = ds.l0_wavelength.data

    return dict
