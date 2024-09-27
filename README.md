# LR-IFS

Compute Lidar Ratio (LR) based on [ECMWF IFS](https://www.ecmwf.int/en/forecasts/documentation-and-support/changes-ecmwf-model) forecasts.

Methodology:
- We use the IFS forecasts data of aerosol optical depth forecasts for the different chemical components.
- For each aerosol species, we calculate a LR weighted by the relative optical depth contribution.
- The total LR is determined as the sum of the weighted LR of the different aerosols species.
  
[Aerosol LR ](config/aerosol_properties.json) for the different species are based on 
  - [Flentje et al., 2021](https://gmd.copernicus.org/articles/14/1721/2021/gmd-14-1721-2021.pdf), at 1064nm (and RH=30% when applicable)
  - [Kim et al., 2018](https://amt.copernicus.org/articles/11/6107/2018/), at 532nm
 

e.g: 2024-09-26

![2024-09-26](examples/lr-1064nm-rh30-20240926.png)


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
> ```
> pip install "git+ssh://git@github.com/AugustinMortier/lr-ifs.git"
> ```

## how to use
Compute LR for the 2024-09-26

```
lr-ifs --date 2024-09-26
```

This will create into `output_path` (default: `./data/`):
- `lr_ifs-20240926.nc`: netcdf file which contains the computed LR.
- `lr_ifs.json` (if `aprofiles` option enabled (default)): json file which contains, for each E-PROFILE station available for the selected day, the corresponding IFS-LR.
