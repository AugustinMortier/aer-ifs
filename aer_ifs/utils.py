import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List

import xarray as xr

import aer_ifs.io.ifs as ifs


class Store(str, Enum):
    storeA = "storeA"
    storeB = "storeB"


def get_config(store: Store) -> dict:
    return {
        "paths": {
            "ifs_od": f"/lustre/{store}/project/fou/kl/CAMS2_35b/cifs-model",
            "ifs_rh_metproduction": f"/lustre/{store}/project/metproduction/products/ecmwf/nc",
            "ifs_rh_archive": f"/lustre/{store}/project/fou/kl/CAMS2_35b/cifs-model",
            "epro": f"/lustre/{store}/project/fou/kl/ceilometer/e-profile",
        },
        "filenames": {
            "ifs_od_00UTC": f"YYYYMMDD_cIFS-00UTC_4vpro_surface.nc",
            "ifs_od_12UTC": f"YYYYMMDD_cIFS-12UTC_o-suite_surface.nc",
            "ifs_rh_metproduction": f"ec_atmo_0_1deg_YYYYMMDDT180000Z_pl.nc",
            "ifs_rh_archive": f"YYYYMMDD_cIFS-00UTC_4vpro_pl1000.nc",
        },
        "vars": [
            "amaod550",
            "bcaod550",
            "duaod550",
            "niaod550",
            "omaod550",
            "ssaod550",
            "suaod550",
        ],
        "wavelengths": [1064, 910, 905, 532],
        "rhs": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    }


def get_aerosol_properties() -> dict:
    # read aerosol_properties.json files
    f = open(Path(Path(__file__).parent, "config", "aerosol_properties.json"))
    return json.load(f)


def get_species_column() -> dict:
    # read species_column.json files
    f = open(Path(Path(__file__).parent, "config", "species_column.json"))
    return json.load(f)


def merge_ifs(od: xr.DataArray, rh: xr.DataArray) -> xr.DataArray:
    # regrid rh on od
    rh_regridded = rh.interp(latitude=od.latitude, longitude=od.longitude)
    return xr.merge([od, rh_regridded])


def ifs_species_lr(species, wav, rh) -> float:
    # return lr for a given species at a given wavelength and rh
    species_column = get_species_column()
    aer_properties = ifs.get_aer_properties()
    i_closest_wav = abs(aer_properties.wavelength.data * 1e9 - wav).argmin()
    i_closest_rh = abs(aer_properties.relative_humidity.data * 1e4 - rh).argmin()

    type = species_column[species]["type"]
    column = species_column[species]["column"]
    if type == "hydrophilic":
        lr = aer_properties[f"lidar_ratio_{type}"][column - 1][i_closest_rh][
            i_closest_wav
        ].data
    elif type == "hydrophobic":
        lr = aer_properties[f"lidar_ratio_{type}"][column - 1][i_closest_wav].data
    return float(lr)


def compute_lr(
    ds: xr.DataArray, vars: List[str], wavs: List[int], rhs: List[int]
) -> xr.DataArray:

    # Create a new DataArray for lr with dimensions 'wav' and 'rh'
    lr = xr.DataArray(
        dims=("wav", "rh", "species", "latitude", "longitude"),
        coords={
            "wav": wavs,
            "rh": rhs,
            "species": [var[:2] for var in vars],
            "latitude": ds["latitude"],
            "longitude": ds["longitude"],
        },
        attrs={"long_name": "Lidar Ratio", "units": "sr"},
    )

    for var in vars:
        ds[f"{var}/aod550"] = ds[var] / ds["aod550"]

    for wav in wavs:
        for rh in rhs:
            for var in vars:
                spec = var[:2]
                lr.loc[dict(wav=wav, rh=rh, species=spec)] = ds[
                    f"{var}/aod550"
                ] * ifs_species_lr(spec, wav, rh)

    # Sum across species to get the total lidar ratio for each wav and rh
    lr_total = lr.sum(dim="species")

    # Assign attributes to the total lidar ratio
    lr_total = lr_total.assign_attrs({"long_name": "Total Lidar Ratio", "units": "sr"})

    # Clean up vars
    for var in vars:
        ds = ds.drop_vars(f"{var}/aod550")

    # Add the computed lr_total to the dataset
    ds["lr"] = lr_total

    return ds


def ifs_species_mec(species, wav, rh) -> float:
    # return mec for a given species at a given wavelength and rh
    species_column = get_species_column()
    aer_properties = ifs.get_aer_properties()
    i_closest_wav = abs(aer_properties.wavelength.data * 1e9 - wav).argmin()
    i_closest_rh = abs(aer_properties.relative_humidity.data * 1e4 - rh).argmin()

    type = species_column[species]["type"]
    column = species_column[species]["column"]
    if type == "hydrophilic":
        lr = aer_properties[f"mass_ext_{type}"][column - 1][i_closest_rh][
            i_closest_wav
        ].data
    elif type == "hydrophobic":
        lr = aer_properties[f"mass_ext_{type}"][column - 1][i_closest_wav].data
    return float(lr)


def compute_mec(
    ds: xr.DataArray, vars: List[str], wavs: List[int], rhs: List[int]
) -> xr.DataArray:

    # Create a new DataArray for mec with dimensions 'wav', 'rh', and 'species'
    mec = xr.DataArray(
        dims=("wav", "rh", "species", "latitude", "longitude"),
        coords={
            "wav": wavs,
            "rh": rhs,
            "species": [var[:2] for var in vars],
            "latitude": ds["latitude"],
            "longitude": ds["longitude"],
        },
        attrs={"long_name": "Mass Extinction Coefficient", "units": "m2 kg-1"},
    )

    for var in vars:
        ds[f"{var}/aod550"] = ds[var] / ds["aod550"]

    for wav in wavs:
        for rh in rhs:
            for var in vars:
                species = var[:2]
                mec.loc[dict(wav=wav, rh=rh, species=species)] = (
                    ds[f"{var}/aod550"] * ifs_species_mec(species, wav, rh) * 1e-3
                )

    # Sum across species to get the total MEC for each wav and rh
    mec_total = mec.sum(dim="species")

    # Assign attributes to the total MEC
    mec_total = mec_total.assign_attrs(
        {"long_name": "Total Mass Extinction Coefficient", "units": "m2 g-1"}
    )

    # Clean up vars
    for var in vars:
        ds = ds.drop_vars(f"{var}/aod550")

    # Add the computed mec_total to the dataset
    ds["mec"] = mec_total

    return ds


def get_closest_station_values(
    ds: xr.DataArray, station_lat: float, station_lon: float
) -> xr.DataArray:
    # Use the sel method with the nearest option to get the closest values
    coloc_ds = ds.sel(latitude=station_lat, longitude=station_lon, method="nearest")
    return coloc_ds


def find_closest_index(arr, target):
    return min(range(len(arr)), key=lambda i: abs(arr[i] - target))


def collocated_dict(ds_ifs: xr.DataArray, dict_apro: dict, vars: List[str]) -> dict:
    # fill up aer_ifs dictionary with closest lr value at right wavelength
    aer_ifs = {}
    for station in dict_apro:
        coloc_ds = get_closest_station_values(
            ds_ifs,
            dict_apro[station].get("station_latitude"),
            dict_apro[station].get("station_longitude"),
        )
        station_wavelength = int(dict_apro[station].get("l0_wavelength"))
        data_dict = {}
        for var in vars:
            data_dict[var] = round(float(coloc_ds[var].data), 4)

        # get index for wavelength
        wavs = coloc_ds["wav"].data
        iwav = wavs.tolist().index(station_wavelength)

        # get index for closest rh
        rhs = coloc_ds["rh"].data
        rh = coloc_ds["relative_humidity_pl"].data
        irh = find_closest_index(rhs, rh)

        aer_ifs[station] = {
            "data": data_dict,
            "lr": round(float(coloc_ds["lr"][iwav][irh].data), 2),
            "mec": round(float(coloc_ds["mec"][iwav][irh].data), 2),
        }

    # add some attributes
    aer_ifs["attributes"] = {
        "default": {"lr": 50, "mec": None},
        "date": datetime.today().strftime("%Y-%m-%d"),
    }
    return aer_ifs
