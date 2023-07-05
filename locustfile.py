from locust import HttpUser, task, between
import numpy as np
import xarray as xr

ds = xr.open_mfdataset("/glade/work/pdas47/cesm-annual/*.nc")
vars = list(ds.keys())
forcing_types = list(ds.coords['forcing_type'].values)
ds.close()


class VizUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def get_ts(self):
        lat = np.random.randint(-90, 90)
        lon = np.random.randint(0, 360)
        
        var = np.random.choice(
            vars
        )
        forcing_type = np.random.choice(
            forcing_types
        )

        self.client.get(f"/ts/?lat={lat:.2f}&lon={lon:.2f}&var={var}&forcing_type={forcing_type}")