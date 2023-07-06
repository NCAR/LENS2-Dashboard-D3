import datetime
import xarray as xr
import pandas as pd
import io
import sys

from dask.distributed import Client, Future

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

DASK_CLUSTER = "localhost:8786"
global_client = Client(DASK_CLUSTER)

print('[!] Loading dataset')
ds = xr.open_mfdataset('data/*.nc', parallel=True, chunks='auto').persist()
ds['time'] = ds.convert_calendar('standard')['time'].dt.year
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

@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse("item.html", {"request": request, "id": id})

async def get_data(
        lat: float,
        lon: float,
        var: str | None = None,
        forcing_type: str | None = None
    ) -> pd.DataFrame:
    async with Client(DASK_CLUSTER, asynchronous=True) as client:
        if var is None:
            ds_subset = ds
        else:
            ds_subset = ds[var]
        
        i_args = dict(
            lat = lat,
            lon = lon,
            method = 'nearest'
        )

        s_args = dict()

        if forcing_type is not None:
            s_args['forcing_type'] = forcing_type
        
        if len(s_args) == 0:
            data = ds_subset.sel(**i_args).to_dask_dataframe().reset_index().drop(['lat', 'lon'], axis=1)
        else:
            data = ds_subset.sel(**i_args).sel(**s_args).to_dask_dataframe().reset_index().drop(['lat', 'lon'], axis=1)

        future: Future = client.compute(data)
        return await future

    

@app.get("/ts/")
async def ts(
    lat: float = 47.6, 
    lon: float = 122.3,
    var: str | None = None,
    forcing_type: str | None = None
    ):
    """Returns time-series data for the requested lat-lon values.
    """
    data = await get_data(lat, lon, var, forcing_type)
    
    # send csv data. https://stackoverflow.com/a/61910803
    stream = io.StringIO()
    data = data[['time', var]]
    data.to_json(stream, orient='index')
    
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/json"
    )  
    del data

    return response