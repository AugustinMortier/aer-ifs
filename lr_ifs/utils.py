
from enum import Enum
from datetime import datetime
import json
import xarray as xr
from typing import List

class Store(str, Enum):
    storeA = "storeA"
    storeB = "storeB"
    
def get_config(store: Store) -> dict:
    return {
        'ifs_path': f'/lustre/{store}/project/fou/kl/CAMS2_35b/cifs-model',
        'vpro_path': f'/lustre/{store}/project/fou/kl/v-profiles',
        'vars': ['amaod550', 'bcaod550', 'duaod550', 'niaod550', 'omaod550', 'ssaod550', 'suaod550']
    }

def get_aer_properties() -> dict:
    return json.load(open('lr_ifs/config/aerosol_properties.json'))

def compute_lr(ds: xr.DataArray, aer_properties: dict, vars: List[str]) -> xr.DataArray:
    
    for var in vars:
        ds[f'{var}/aod550'] = ds[var] / ds['aod550']

    for wav in aer_properties:
        for rh in aer_properties[wav]:
            key_vars = []
            for var in vars:
                species = var[:2]
                ds[f'lr-{species}-{wav}-{rh}'] = ds[f'{var}/aod550'] * aer_properties[wav][rh][species]
                key_vars.append(f'lr-{species}-{wav}-{rh}')
            ds[f'lr-{wav}-{rh}'] = sum(ds[key_var] for key_var in key_vars)
            ds[f'lr-{wav}-{rh}'] = ds[f'lr-{wav}-{rh}'].assign_attrs({
                'long_name': f'Lidar Ratio at {wav}nm and RH: {rh}%',
                'units': 'sr'
            })

    # clean up vars
    for var in vars:
        ds = ds.drop_vars(f'{var}/aod550')
        for wav in aer_properties:
            for rh in aer_properties[wav]:
                species = var[:2]
                ds = ds.drop_vars(f'lr-{species}-{wav}-{rh}')
    return ds

def get_closest_station_values(ds: xr.DataArray, station_lat: float, station_lon: float) -> xr.DataArray:
    # Use the sel method with the nearest option to get the closest values
    coloc_ds = ds.sel(latitude=station_lat, longitude=station_lon, method='nearest')
    return coloc_ds

def collocated_dict(ds_ifs: xr.DataArray , dict_apro: dict, vars: List[str]) -> dict:
    # fill up lr_ifs dictionary with closest lr value at right wavelength
    lr_ifs = {}
    for station in dict_apro:
        coloc_ds = get_closest_station_values(ds_ifs, dict_apro[station].get('station_latitude'), dict_apro[station].get('station_longitude'))
        station_wavelength = int(dict_apro[station].get('l0_wavelength'))
        data_dict = {}
        for var in vars:
            data_dict[var] = round(float(coloc_ds[var].data), 4)
        lr_ifs[station] = {
            'data': data_dict,
            'apriori': {
                'lr': round(float(coloc_ds[f'lr-{station_wavelength}-rh30'].data), 2)
            }
        }
    
    # add some attributes
    lr_ifs['attributes'] = {
        "default": {
            "apriori": {
                "lr": 50
            }
        },
        "date": datetime.today().strftime('%Y-%m-%d')
    }
    return lr_ifs
    