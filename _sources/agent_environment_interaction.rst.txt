Agent-environment interaction
###############################

Honeybees contains several functions to very quickly sample data from maps. The example belows shows an example sampling from a NumPy array directly using :func:`honeybees.library.raster.sample_from_map`, and from a GeoTIFF file using :class:`honeybees.library.mapIO.ArrayReader`. You can also use :class:`honeybees.library.mapIO.NetCDFReader`.


.. code-block:: python

    from datetime import date
    import os
    from dateutil.relativedelta import relativedelta

    import numpy as np
    import rasterio

    from honeybees.model import Model
    from honeybees.area import Area
    from honeybees.reporter import Reporter
    from honeybees.agents import AgentBaseClass

    from honeybees.library.raster import sample_from_map
    from honeybees.library.mapIO import ArrayReader

    MAP = np.random.random(100 ** 2).reshape(100, 100)
    MAP_GEOTRANSFORM = (-10, 0.2, 0, 10, 0, -.2)

    class People(AgentBaseClass):
        def __init__(self, model, agents):
            self.n = 1000
            self.model = model
            self.agents = agents
            self.age = np.random.randint(0, 100, self.n)
            self.locations = np.zeros((self.n, 2), dtype=np.float32)
            self.set_locations()

            self.data = ArrayReader('examples/random.tif', bounds=self.model.bounds)

        def set_locations(self):
            self.locations[:, 0] = np.random.uniform(self.model.xmin, self.model.xmax, self.n)
            self.locations[:, 1] = np.random.uniform(self.model.ymin, self.model.ymax, self.n)

        def step(self):
            values_from_array = sample_from_map(MAP, self.locations, MAP_GEOTRANSFORM)
            values_from_GTiff = self.data.sample_coords(self.locations)

    class Agents(AgentBaseClass):
        def __init__(self, model):
            self.people = People(model, self)

        def step(self):
            self.people.step()

    class ABMModel(Model):
        def __init__(self, config_path, study_area, args=None):
            self.area = Area(self, study_area)
            self.agents = Agents(self)
            
            current_time = date(2020, 1, 1)
            timestep_length = relativedelta(years=1)
            n_timesteps = 10
            
            Model.__init__(self, current_time, timestep_length, config_path, args=args, n_timesteps=n_timesteps)

            self.reporter = Reporter(self)


    if __name__ == '__main__':
        fp = 'examples/random.tif'
        with rasterio.open(fp, 'w', driver='GTiff', height=MAP.shape[0], width=MAP.shape[1], count=1, dtype=MAP.dtype, transform=rasterio.Affine.from_gdal(*MAP_GEOTRANSFORM)) as dst:
            dst.write(MAP, 1)
        
        config_path = 'examples/config.yml'
        study_area = {
            'xmin': -10,
            'xmax': 10,
            'ymin': -10,
            'ymax': 10
        }
        model = ABMModel(config_path, study_area)

        for _ in range(1):
            model.step()

        if os.path.exists(fp):
            del model.agents.people.data
            os.remove(fp)