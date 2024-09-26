import typer
from datetime import datetime
import json
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
    for _i in (track(range(1), description=f':robot: Reading IFS data',disable=not verbose)):
        ds_ifs = ifs.read(CFG.get('ifs_path'), date)

    # get aerosol properties
    aer_properties = utils.get_aer_properties()
    
    # compute lr
    for _i in (track(range(1), description=f':computer: Compute LR from IFS data',disable=not verbose)):
        ds_ifs = utils.compute_lr(ds_ifs, aer_properties, CFG['vars'])

    # write file
    for _i in (track(range(1), description=f':floppy_disk: Writing netcdf file',disable=not verbose)):
        path_output = Path(output, date.strftime('%Y'), date.strftime('%m'))
        path_output.mkdir(parents=True, exist_ok=True)
        ds_ifs.to_netcdf(Path(path_output, f"lr_ifs-{date.strftime('%Y%m%d')}.nc"), mode='w')
    
    if aprofiles:
        # open aprofiles files of the day
        dict_apro = apro.read(CFG.get('vpro_path'), date, verbose)

        # fill up lr_ifs dictionary with closest lr value at right wavelength
        lr_ifs = utils.collocated_dict(ds_ifs, dict_apro, CFG['vars'])
        
        # write file
        for _i in (track(range(1), description=f':floppy_disk: Writing json file',disable=not verbose)):
            file_path = Path(path_output , f"lr_ifs-{date.strftime('%Y%m%d')}.json")
            with file_path.open('w') as json_file:
                json.dump(lr_ifs, json_file, indent=4)

if __name__ == "__main__":
    app()