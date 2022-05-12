---
title: QartodNems
description: Automated NEMS Coding of Continuous Data. A Jupyter Notebook and associated python functions to automatically clean and quality code continuous data to NEMS standards.
---

## QartodNems

---
An initial set of scripts for cleaning and coding continuous data to NEMS. 
Based on Qartod IOOS standards and code with NEMS functions added.

Current implementation is built to run off Hilltop Timeseries servers, but there are placeholders in the code for other server types to be used to access the data.

Generates a csv output that can be imported into Hilltop databases (not tested against other systems). 

## Features


## Usage
See Installation section for details of installing the files and dependencies.

### Starting 
Open the miniconda command prompt and navigate to the directory containing the files.  You'll need to activate the environment in order for the scripts to work.

#### Activate the environment
To activate the environment (make it so that scripts run use the environment and packages in it)

`conda activate ioos_nems`

#### Start the notebook
Once the environement is active start the jupyter notebook by entering

`jupyter notebook`

in the command line and selecting the default browser you want to open it with.

### Ending
The below are done from the miniconda command prompt.

#### Stop the notebook 
From the command line press Ctrl C

#### Deactivate the environment
to deactivate the environment

`conda deactivate`

### Using the notebook
With the ioos_nems environment running and the notebook started.

From the jupyter homepage open the notebook, file HAWQiWidgetVer.ipynb

Press the option Restart and run all.

Select the site and measurement to process.

Summary graphs of the results will show, and a csv of processed data will be created.

## Requirements

The ioos-qc package now has a requirement for geopandas.  There are known problems installing this on a Windows machine due to dependencies and setup requirements.
The recommended installation method is using conda.

Conda or miniconda will need to be installed on the machine used to run the script.  The environment will need to be running a recent version of Python3.

The environment.yml file provides a list of the packages that need to be installed in the environment, see the 'Installation' section below.

### Data Files





### Configuration Files

These files allow some customisation of the app.

#### WQMeasurements.csv





## Installation
The ioos-qc package now has a requirement for geopandas.  There are known problems installing this on a Windows machine due to dependencies and setup requirements.
The recommended installation method is using conda.

The environment.yml file provides the information required to setup an ioos_nems environment that will allow the qartodNems notebooks and scripts to run.

1. Install miniconda (with python version 3.8) [Miniconda Installers](https://docs.conda.io/en/latest/miniconda.html)
2. Clone or download this repository to your local machine.
3. From the miniconda command prompt navigate to the directory that contains the files and run 

`conda env create -f environment.yml`

To update run

`conda env update --file environment.yml  --prune`

## Project Status

## Goals/Roadmap

## Getting Help or Reporting an Issue

## How to Contribute



## License

MIT



