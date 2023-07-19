import datetime
import xarray as xr
import pandas as pd
import io
import sys
import json
from datashader.utils import lnglat_to_meters

from dask.distributed import Client, Future

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

templates = Jinja2Templates(directory="d3-CESM-tiling/templates")

app.mount("/d3-CESM-tiling/static", StaticFiles(directory="static"), name="static")

DASK_CLUSTER = "localhost:8786"
global_client = Client(DASK_CLUSTER)

print('[!] Loading dataset')
# ds = xr.open_mfdataset('data/*.nc', parallel=True, chunks='auto').persist()
ds = xr.open_mfdataset('d3-CESM-tiling/static/data/*.nc', parallel=True, chunks='auto') # preprocessed to meters lat-lng

CURRENT_VARIABLE = "TS"
FORCING = "cmip6"
COLORLIM = (
        float(ds[CURRENT_VARIABLE].min()),
        float(ds[CURRENT_VARIABLE].max())
    )
YEAR = 2023

print('[!] Dataset loaded')

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "todays_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "var_list": list(ds.keys()),
            "forcing_types": list(ds.coords["forcing_type"].values)
        }
    )

@app.get("/dataset/{variable}")
def set_dataset(variable):
    global CURRENT_VARIABLE
    CURRENT_VARIABLE = variable
    return ''

@app.get("/dims/{year}/{forcing}")
def set_dims(year, forcing):
    global YEAR
    global FORCING
    global COLORLIM

    YEAR = int(year)
    FORCING = forcing
    COLORLIM = (
        float(ds[CURRENT_VARIABLE].min()),
        float(ds[CURRENT_VARIABLE].max())
    )

    return ''

async def get_data(
        lat: float,
        lon: float,
        var: str | None = None,
        forcing_type: str | None = None
    ) -> pd.DataFrame:
    async with Client(DASK_CLUSTER, asynchronous=True) as client:
        ds_subset = ds[CURRENT_VARIABLE].sel(forcing_type=FORCING)
        
        i_args = dict(
            y = lat,
            x = lon,
            method = 'nearest'
        )
        data = ds_subset.sel(**i_args).to_dask_dataframe().reset_index().drop(['x', 'y'], axis=1)

        future: Future = client.compute(data)
        return await future

async def get_tile_data(
        xmin: float, 
        ymin: float, 
        xmax: float, 
        ymax: float
    ) -> pd.DataFrame:
    async with Client(DASK_CLUSTER, asynchronous=True) as client:
        data_subset = ds[CURRENT_VARIABLE] \
                        .sel(forcing_type=FORCING) \
                        .sel(time=YEAR)
        data_subset = data_subset.query(
            x = f"x >= {xmin} and x <= {xmax}",
            y = f"y >= {ymin} and y <= {ymax}",
        )
        
        future: Future = client.compute(data_subset)

        return await future

@app.get("/tiles/{xmax}/{ymax}/{xmin}/{ymin}")
async def get_tile(xmax, ymax, xmin, ymin): # TODO: potentially reorder the coordinates as xmin, ymin, xmax, ymax (more standard configuration)
    xmin, ymin, xmax, ymax = [float(n) for n in (xmin, ymin, xmax, ymax)]
    xmin_m, ymin_m = lnglat_to_meters(xmin, ymin)
    xmax_m, ymax_m = lnglat_to_meters(xmax, ymax)

    data_subset = await get_tile_data(xmin_m, ymin_m, xmax_m, ymax_m)

    data_df = data_subset.to_dataframe().reset_index()

    cornerpoints = (xmin_m, ymin_m, xmax_m, ymax_m)

    json_data = {
        'data': data_df.to_json(orient='table'),
        'cornerpoints': cornerpoints,
        'colorlim': COLORLIM
    }

    return Response(
        content = json.dumps(json_data),
        media_type="application/json"
    )
    

@app.get("/ts/{lat}/{lon}")
async def ts(
    lat: float = 47.6, 
    lon: float = 122.3,
    ):
    """Returns time-series data for the requested lat-lon values.
    """
    data = await get_data(lat, lon)
    
    # send csv data. https://stackoverflow.com/a/61910803
    data = data[['time', CURRENT_VARIABLE]]

    response = Response(
        content=data.to_json(orient='table'),
        media_type="application/json"
    )
    del data

    return response

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000)