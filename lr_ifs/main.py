import typer
from datetime import datetime
from pathlib import Path
from rich.progress import track


import lr_ifs.utils as utils
import lr_ifs.io.ifs as ifs
import lr_ifs.io.apro as apro


app = typer.Typer()

@app.command()
def main(
        date: datetime=datetime.today(),
        aprofiles: bool=True,
        store: utils.Store='storeB',
        output: Path='./data/',
        verbose: bool=True
    ):
    
    CFG = utils.get_config(store)
    
    # read ifs od-speciated model
    for _i in (track(range(1), description=f':book: Reading IFS data',disable=not verbose)):
        ds_ifs = ifs.read(CFG.get('ifs_path'), date)

    # get aerosol properties
    aer_properties = utils.get_aer_properties()
    
    # compute lr
    for _i in (track(range(1), description=f':computer: Compute LR from IFS data',disable=not verbose)):
        ds_ifs = utils.compute_lr(ds_ifs, aer_properties)

    # write file
    path_output = Path(output, date.strftime('%Y'), date.strftime('%m'), date.strftime('%d'))
    path_output.mkdir(parents=True, exist_ok=True)
    ds_ifs.to_netcdf(Path(path_output, f"lr_ifs-{date.strftime('%Y%m%d')}.nc"), mode='w')
    
    if aprofiles:
        # open aprofiles files of the day
        dict_apro = apro.read(CFG.get('vpro_path'), date, verbose)

        # fill up lr_ifs dictionary with closest lr value at right wavelength
        lr_ifs = {}
        for station in dict_apro:
            coloc_ds = utils.get_closest_station_values(ds_ifs, dict_apro[station].get('station_latitude'), dict_apro[station].get('station_longitude'))
            station_wavelength = int(dict_apro[station].get('l0_wavelength'))
            lr_ifs[station] = {
                'data': coloc_ds.to_dict(),
                'apriori': {
                    'lr': float(coloc_ds[f'lr-{station_wavelength}-rh30'].data)
                }
            }

if __name__ == "__main__":
    app()