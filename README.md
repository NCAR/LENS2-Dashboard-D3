# LENS2-Dashboard

This repository hosts the code for a dashboard for the [LENS2](https://www.cesm.ucar.edu/community-projects/lens2) dataset using [FastAPI](https://fastapi.tiangolo.com/) and [D3.js](https://d3js.org/).

To get started, clone this repository using `git clone --recurse-submodules https://github.com/NCAR/LENS2-Dashboard-D3.git`

## Recreating the environment
The `environment.yml` will allow you to recreate the environment required for this project. You will need `conda` installed, which you can find [here](https://docs.conda.io/en/latest/miniconda.html). [This tutorial on conda](https://foundations.projectpythia.org/foundations/conda.html) by [ProjectPythia](https://projectpythia.org/) will help you install and understand the basics of environment management with conda.

Once you have conda installed, you can use the following commands to recreate the environment.
1. `cd LENS2-Dashboard-D3 && conda create --prefix ./.env -c conda-forge mamba`  This will create a directory called `.env` in your local copy of the `LENS2-Dashboard-D3` repository and install `mamba` in it. `mamba` is faster than conda in solving environments.
1. `conda activate ./.env && mamba env update --file environment.yml --prefix ./.env` - This will start creating the environemnt in the `.env` directory based on the `environment.yml` file. 
1. `conda activate ./.env` and voila! you just activated the environment required to run the back-end server. You will still need t

## Get the d3-CESM-tiling submodule (if did not use `--recurse-submodules` while cloning the repository)
This back-end is tied to the front-end code hosted at the [NCAR/d3-CESM-tiling](`https://github.com/NCAR/d3-CESM-tiling`) repository. The back-end imports this code as a [git submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules). The submodule contents can either be fetched during cloning the back-end this repository by specifying the `--recurse-submodules` flag, or manually by executing the following command: 
`git submodule update --init`


## How to start the back-end server
Once you have the environment activated, the following commands are required to (1) start a dask cluster, (2) start some dask workers, and (3) start the fastapi server.

### Scheduler
`dask scheduler --host localhost --port 8786`

### Workers - 16 workers, 2GiB memory
`dask worker --host localhost --nworkers 16 --memory-limit '2GB' localhost:8786`

### Run the server in development mode - if you're modifying the back-end code
`uvicorn --reload app:app`

### Run the server in production mode - if you're hosting the back-end server in production
`gunicorn -k uvicorn.workers.UvicornWorker app:app`