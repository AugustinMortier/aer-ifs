# LR-IFS

Compute Lidar Ratio (LR) based on [ECMWF IFS](https://www.ecmwf.int/en/forecasts/documentation-and-support/changes-ecmwf-model) forecasts.

Methodology:
- We get the IFS forecasts data of **aerosol optical depth** forecasts for the different chemical components.
- We get the IFS forecasts data of **relative humidity**.
- For each aerosol species, we calculate a **LR weighted** by the relative optical depth contribution for different RH values.
- The total LR is determined as the **sum of the weighted LR** of the different aerosols species.
  
Individual [aerosol LR](lr_ifs/config/aerosol_properties.json) for the different species are based on 
  - [Flentje et al., 2021](https://gmd.copernicus.org/articles/14/1721/2021/gmd-14-1721-2021.pdf), at 1064nm (RH dependent)
  - [Kim et al., 2018](https://amt.copernicus.org/articles/11/6107/2018/), at 532nm (ambient RH)
 
## example

```
lr-ifs --date 2024-10-04
```

<figure id="examples">
  <div id="panel" float="left">
    <img src="examples/lr-1064nm-rh30-20241004.png" width="49%">
    <img src="examples/lr-1064nm-rh80-20241004.png" width="49%">
  </div>
  <figcaption>Fig 1: IFS LR - 2024-10-04 - 1064 nm</figcaption>
</figure>


## get started

### 1. clone repo
```
git clone https://github.com/AugustinMortier/lr-ifs.git
```

### 2. install
- via poetry
```
poetry install
```

- via pip/pipx
```
pip install .
```

> [!NOTE]
> You can also install lr-ifs with this one liner:
> ```
> pip install "git+ssh://git@github.com/AugustinMortier/lr-ifs.git"
> ```

## how to use
Compute LR for the 2024-09-26

```
lr-ifs --date 2024-09-26
```

This will create into `output_path` (default: `./data/`):
- `{yyyy}/{mm}/lr_ifs-{yyyymmdd}.nc`: netcdf file which contains the computed LR.
- `{yyyy}/{mm}/lr_ifs-{yyyymmdd}.json` (if `aprofiles` option enabled (default)): json file which contains, for each E-PROFILE station available and for the selected day, the corresponding IFS-LR.

## limitations
- Due to OD definition, the computed LR is an averaged value over the **whole atmospheric column**.
- Only **one value per day** is computed at the moment and corresponds to **00:00:00Z**.
- When applicable (1064nm), only the **RH at the surface** level is considered.
