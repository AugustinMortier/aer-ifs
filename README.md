# LR-IFS

Compute Lidar Ratio based on ECMWF IFS data.

Methodology:
- We use the IFS forecasts data of optical depth forecasts for the different chemical species.
- For each species, we calculate a lidar ratio weighted by the relative optical depth contribution, based on [Flentje et al., 2021](https://gmd.copernicus.org/articles/14/1721/2021/gmd-14-1721-2021.pdf) (currently at 1064nm, RH: 30%)

e.g:

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

## basic use
Compute LR for the 2024-09-26

```
lr-ifs --date 2024-09-26
```

This will create into `output_path` (default: `./data/`):
- `lr_ifs-20240926.nc`: netcdf file which contains the computed Lidar Ratio.
- `lr_ifs.json` (if `aprofiles` option enabled (default)): json file which contains, for each E-PROFILE station available for the selected day, the corresponding IFS-LR.