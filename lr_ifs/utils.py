
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

    for key in aer_properties:
        key_vars = []
        for var in vars:
            species = var[:2]
            ds[f"lr-{species}-{key}"] = ds[f"{var}/aod550"] * aer_properties["1064nm-rh30"][species]
            key_vars.append(f"lr-{species}-{key}")
        ds[f"lr-{key}"] = sum(ds[key_var] for key_var in key_vars)

    # clean up vars
    ds = ds.drop_vars([f"{var}/aod550" for var in vars] + [f"lr-{var[:2]}-{key}" for var in vars for key in aer_properties])

    return ds
