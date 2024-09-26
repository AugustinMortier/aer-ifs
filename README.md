# LR-IFS

Compute Lidar Ratio (LR) based on [ECMWF IFS](https://www.ecmwf.int/en/forecasts/documentation-and-support/changes-ecmwf-model) forecasts.

Methodology:
- We use the IFS forecasts data of optical depth forecasts for the different chemical species.
- For each species, we calculate a lidar ratio weighted by the relative optical depth contribution, based on 
  - [Flentje et al., 2021](https://gmd.copernicus.org/articles/14/1721/2021/gmd-14-1721-2021.pdf), at 1064nm
  - [Kim et al., 2018](https://amt.copernicus.org/articles/11/6107/2018/), at 532nm

> [!NOTE]
> Lidar Ratios of [chemical species](lr_ifs/config/aerosol_properties.json) at 1064 nm are provided at RH=30%.
 

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

- via pip
```
pip install
```

## how to use
Compute LR for the 2024-09-26

```
lr-ifs --date 2024-09-26
```

This will create into `output_path` (default: `./data/`):
- `lr_ifs-20240926.nc`: netcdf file which contains the computed LR.
- `lr_ifs.json` (if `aprofiles` option enabled (default)): json file which contains, for each E-PROFILE station available for the selected day, the corresponding IFS-LR.
