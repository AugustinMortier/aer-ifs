import json
from datetime import datetime
from pathlib import Path

import typer
from rich.progress import track
from typing_extensions import Annotated

import aer_ifs.io.apro as apro
import aer_ifs.io.ifs as ifs
import aer_ifs.utils as utils

app = typer.Typer()


@app.command()
def main(
    date: Annotated[datetime, typer.Option(help="date")] = datetime.today(),
    aprofiles: Annotated[
        bool, typer.Option(help="process lr at aprofiles collocated stations")
    ] = True,
    store: Annotated[utils.Store, typer.Option(help="ppi store system")] = "storeB",
    output: Annotated[Path, typer.Option(help="output path")] = "./data/",
    verbose: Annotated[bool, typer.Option(help="verbose mode")] = True,
):
    CFG = utils.get_config(store)

    # read ifs od-speciated model
    for _i in track(
        range(1), description=f":robot: Reading IFS OD data", disable=not verbose
    ):
        od_ifs = ifs.read_od(date, CFG)

    # read ifs rh
    for _i in track(
        range(1), description=f":robot: Reading IFS RH data", disable=not verbose
    ):
        rh_ifs = ifs.read_rh(date, CFG)

    # merge two datasets
    ds_ifs = utils.merge_ifs(od_ifs, rh_ifs)

    # compute lr
    for _i in track(
        range(1),
        description=f":computer: Compute LR from IFS data",
        disable=not verbose,
    ):
        ds_ifs = utils.compute_lr(ds_ifs, CFG["vars"], CFG["wavelengths"], CFG["rhs"])

    # compute mec
    for _i in track(
        range(1),
        description=f":computer: Compute MEC from IFS data",
        disable=not verbose,
    ):
        ds_ifs = utils.compute_mec(ds_ifs, CFG["vars"], CFG["wavelengths"], CFG["rhs"])

    # write file
    for _i in track(
        range(1), description=f":floppy_disk: Writing netcdf file", disable=not verbose
    ):
        path_output = Path(output, date.strftime("%Y"), date.strftime("%m"))
        path_output.mkdir(parents=True, exist_ok=True)
        ds_ifs.to_netcdf(
            Path(path_output, f"aer_ifs-{date.strftime('%Y%m%d')}.nc"), mode="w"
        )

    if aprofiles:
        # open aprofiles files of the day
        dict_apro = apro.read(CFG.get("paths").get("epro"), date, verbose)

        # fill up aer_ifs dictionary with closest lr value at right wavelength
        aer_ifs = utils.collocated_dict(
            ds_ifs, dict_apro, CFG["vars"] + ["relative_humidity_pl"]
        )

        # write file
        for _i in track(
            range(1),
            description=f":floppy_disk: Writing json file",
            disable=not verbose,
        ):
            file_path = Path(path_output, f"aer_ifs-{date.strftime('%Y%m%d')}.json")
            with file_path.open("w") as json_file:
                json.dump(aer_ifs, json_file, indent=4)


if __name__ == "__main__":
    app()
