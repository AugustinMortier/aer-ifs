
from enum import Enum
import json
import xarray as xr

class Store(str, Enum):
    storeA = "storeA"
    storeB = "storeB"
    
def get_config(store: Store) -> dict:
    CFG = {
        'ifs_path': f'/lustre/{store}/project/fou/kl/CAMS2_35b/cifs-model',
        'vpro_path': f'/lustre/{store}/project/fou/kl/v-profiles',
    }
    return CFG

def get_aer_properties() -> dict:
    return json.load(open('lr_ifs/config/aerosol_properties.json'))

def compute_lr(ds: xr.DataArray, aer_properties: dict) -> xr.DataArray:
    vars = ['amaod550', 'bcaod550', 'duaod550', 'niaod550', 'omaod550', 'ssaod550', 'suaod550']
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