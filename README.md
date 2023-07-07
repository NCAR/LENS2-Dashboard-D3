# LENS2-Dashboard
A repository for SIParCS Lens2 visualization project. 

## Recreating the environment
the `environment.yml` should allow you to recreate the conda environment required for this project. You can find `miniconda` [here](https://docs.conda.io/en/latest/miniconda.html) if you don't have conda installed. [This tutorial on conda](https://foundations.projectpythia.org/foundations/conda.html) by [ProjectPythia](https://projectpythia.org/) should help you install and understand the basics of environment management with conda.

Once you have conda installed, you can use the following commands to recreate the environment.
1. `cd <project_directory> && conda create --prefix ./.env -c conda-forge mamba` - This will create a directory called `.env` in your `<project_directory>` and install `mamba` in it. `mamba` is faster than conda in solving environments.
1. `conda activate ./.env && mamba env update --file environment.yml --prefix ./.env` - This will start creating the environemnt in the `.env` directory based on the `environment.yml` file. 
1. `conda activate ./.env` and voila! This will activate the environment, hopefully with everything that you need installed. The following instructions can now be followed to start the server.

## How to start the backend server
Once you have the environment activated, the following commands are required to (1) start a dask cluster, (2) start some dask workers, and (3) start the fastapi server.

### Scheduler
`dask scheduler --host localhost --port 8786`

### Workers - 16 workers, 2GiB memory
`dask worker --host localhost --nworkers 16 --memory-limit '2GB' localhost:8786`

### FastAPI
`uvicorn --reload app:app`