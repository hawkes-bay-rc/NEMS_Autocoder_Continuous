# QartodNems
This is the preprocessor on the data in a trial mode
The data is fetched from hilltop api
The code is oriented towards processing HAWQi data

Since NBviewer on the Github doesn't allow dynamic html,
The current notebook has a limited functionality here.

A binder version will be made available at the earliest

The QaBay is the core module doing the heavy lifting
The hillDepth, by Jeff cooke does the retrieval of periodic observations
The widgetVer in addition to above to modules produces the results

## Local Installation
The ioos-qc package now has a requirement for geopandas.  There are known problems installing this on a Windows machine due to dependencies and setup requirements.
The recommended installation method is using conda.

The environment.yml file provides the information required to setup an ioos_nems environment that will allow the qartodNems notebooks and scripts to run.

1. Install miniconda (with python version 3.8) [Miniconda Installers](https://docs.conda.io/en/latest/miniconda.html)
2. Clone or download this repository to your local machine.
3. From the miniconda command prompt navigate to the directory that contains the files and run 

`conda env create -f environment.yml`

To update run

`conda env update --file environment.yml  --prune`

## Getting Started
Open the miniconda command prompt and navigate to the directory containing the files.  You'll need to activate the environment in order for the scripts to work.

### Activate the environment
To activate the environment (make it so that scripts run use the environment and packages in it)

`conda activate ioos_nems`

### Start the notebook
Once the environement is active start the jupyter notebook by entering

`jupyter notebook`

in the command line and selecting the default browser you want to open it with.

### Stop the notebook 
From the command line press Ctrl C

### Deactivate the environment
to deactivate the environment

`conda deactivate`

## Using the notebook
With the ioos_nems environment running and the notebook started.

From the jupyter homepage open the notebook, file HAWQiWidgetVer.ipynb

Press the option Restart and run all.

Select the site and measurement to process.

Summary graphs of the results will show, and a csv of processed data will be created.
