
from enum import Enum
from datetime import datetime
import json
from pathlib import Path
import xarray as xr
from typing import List
import aer_ifs.io.ifs as ifs

class Store(str, Enum):
    storeA = "storeA"
    storeB = "storeB"
    
def get_config(store: Store) -> dict:
    return {
        'ifs_od_path': f'/lustre/{store}/project/fou/kl/CAMS2_35b/cifs-model',
        'ifs_rh_path': f'/lustre/{store}/project/metproduction/products/ecmwf/nc',
        'vpro_path': f'/lustre/{store}/project/fou/kl/v-profiles',
        'vars': ['amaod550', 'bcaod550', 'duaod550', 'niaod550', 'omaod550', 'ssaod550', 'suaod550'],
        'wavelengths': [1064, 905, 532],
        'rhs': [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    }

def get_aerosol_properties() -> dict:
    # read aerosol_properties.json files
    f = open(Path(Path(__file__).parent,'config','aerosol_properties.json'))
    return json.load(f)

def get_species_column() -> dict:
    # read species_column.json files
    f = open(Path(Path(__file__).parent,'config','species_column.json'))
    return json.load(f)

def merge_ifs(od: xr.DataArray, rh: xr.DataArray) -> xr.DataArray:
    # regrid rh on od
    rh_regridded = rh.interp(
        latitude=od.latitude, longitude=od.longitude
    )
    return xr.merge([od, rh_regridded])

def ifs_species_lr(species, wav, rh) -> float:
    # return lr for a given species at a given wavelength and rh
    species_column = get_species_column()
    aer_properties = ifs.get_aer_properties()
    i_closest_wav = abs(aer_properties.wavelength.data * 1e9 - wav).argmin()
    i_closest_rh = abs(aer_properties.relative_humidity.data * 1e4 - rh).argmin()

    type = species_column[species]['type']
    column = species_column[species]['column']
    if type == 'hydrophilic':
        lr = aer_properties[f'lidar_ratio_{type}'][column - 1][i_closest_rh][i_closest_wav].data
    elif type == 'hydrophobic':
        lr = aer_properties[f'lidar_ratio_{type}'][column - 1][i_closest_wav].data
    return float(lr)

def compute_lr(ds: xr.DataArray, vars: List[str], wavs: List[int], rhs: List[int]) -> xr.DataArray:
    
    for var in vars:
        ds[f'{var}/aod550'] = ds[var] / ds['aod550']

    for wav in wavs:
        for rh in rhs:
            key_vars = []
            for var in vars:
                species = var[:2]
                ds[f'lr-{species}-{wav}-{rh}'] = ds[f'{var}/aod550'] * ifs_species_lr(species, wav, rh)
                key_vars.append(f'lr-{species}-{wav}-{rh}')
            ds[f'lr-{wav}-{rh}'] = sum(ds[key_var] for key_var in key_vars)
            ds[f'lr-{wav}-{rh}'] = ds[f'lr-{wav}-{rh}'].assign_attrs({
                'long_name': f'Lidar Ratio at {wav}nm and RH: {rh}%',
                'units': 'sr'
            })

    # clean up vars
    for var in vars:
        species = var[:2]
        ds = ds.drop_vars(f'{var}/aod550')
        for wav in wavs:
            for rh in rhs:
                ds = ds.drop_vars(f'lr-{species}-{wav}-{rh}')
    return ds

def ifs_species_mec(species, wav, rh) -> float:
    # return mec for a given species at a given wavelength and rh
    species_column = get_species_column()
    aer_properties = ifs.get_aer_properties()
    i_closest_wav = abs(aer_properties.wavelength.data * 1e9 - wav).argmin()
    i_closest_rh = abs(aer_properties.relative_humidity.data * 1e4 - rh).argmin()

    type = species_column[species]['type']
    column = species_column[species]['column']
    if type == 'hydrophilic':
        lr = aer_properties[f'mass_ext_{type}'][column - 1][i_closest_rh][i_closest_wav].data
    elif type == 'hydrophobic':
        lr = aer_properties[f'mass_ext_{type}'][column - 1][i_closest_wav].data
    return float(lr)

def compute_mec(ds: xr.DataArray, vars: List[str], wavs: List[int], rhs: List[int]) -> xr.DataArray:
    
    for var in vars:
        ds[f'{var}/aod550'] = ds[var] / ds['aod550']

    for wav in wavs:
        for rh in rhs:
            key_vars = []
            for var in vars:
                species = var[:2]
                ds[f'mec-{species}-{wav}-{rh}'] = ds[f'{var}/aod550'] * ifs_species_mec(species, wav, rh)
                key_vars.append(f'mec-{species}-{wav}-{rh}')
            ds[f'mec-{wav}-{rh}'] = sum(ds[key_var] for key_var in key_vars)
            ds[f'mec-{wav}-{rh}'] = ds[f'mec-{wav}-{rh}'].assign_attrs({
                'long_name': f'MEC at {wav}nm and RH: {rh}%',
                'units': 'm2 kg-1'
            })

    # clean up vars
    for var in vars:
        species = var[:2]
        ds = ds.drop_vars(f'{var}/aod550')
        for wav in wavs:
            for rh in rhs:
                ds = ds.drop_vars(f'mec-{species}-{wav}-{rh}')
    return ds

def get_closest_station_values(ds: xr.DataArray, station_lat: float, station_lon: float) -> xr.DataArray:
    # Use the sel method with the nearest option to get the closest values
    coloc_ds = ds.sel(latitude=station_lat, longitude=station_lon, method='nearest')
    return coloc_ds

def get_closest_key(ds, wav):
    # list variables matching wav (use lr, but could use mec instead)
    variables = [var for var in list(ds.variables) if var.startswith(f'lr-{wav}')]
    # relative humidity
    rh_value = float(ds['relative_humidity_pl'].data)
    # Step 1: Extract RH values by splitting the string
    rh_values = [int(s.split('-')[2]) for s in variables]
    # Step 2: Find the index of the closest RH value
    closest_index = min(range(len(rh_values)), key=lambda i: abs(rh_values[i] - rh_value))
    # Step 3: Get the corresponding string
    closest_string = variables[closest_index]
    # Step 4: Remove lr part 
    return closest_string.split('lr-')[1]

def collocated_dict(ds_ifs: xr.DataArray , dict_apro: dict, vars: List[str]) -> dict:
    # fill up aer_ifs dictionary with closest lr value at right wavelength
    aer_ifs = {}
    for station in dict_apro:
        coloc_ds = get_closest_station_values(ds_ifs, dict_apro[station].get('station_latitude'), dict_apro[station].get('station_longitude'))
        station_wavelength = int(dict_apro[station].get('l0_wavelength'))
        data_dict = {}
        for var in vars:
            data_dict[var] = round(float(coloc_ds[var].data), 4)
        
        # get closest rh to available keys
        key = get_closest_key(coloc_ds, station_wavelength)
        
        aer_ifs[station] = {
            'data': data_dict,
            'apriori': {
                'lr': round(float(coloc_ds[f'lr-{key}'].data), 2),
                'mec': round(float(coloc_ds[f'mec-{key}'].data), 2),
            }
        }
    
    # add some attributes
    aer_ifs['attributes'] = {
        "default": {
            "apriori": {
                "lr": 50,
                "mec": None
            }
        },
        "date": datetime.today().strftime('%Y-%m-%d')
    }
    return aer_ifs
    