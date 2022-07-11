Visualisation
###############

Honeybees also features a visualization module. An example of how to use it is given below.

.. code-block:: python

    from datetime import date
    from dateutil.relativedelta import relativedelta
    import numpy as np

    from honeybees.model import Model
    from honeybees.area import Area
    from honeybees.reporter import Reporter
    from honeybees.agents import AgentBaseClass
    from honeybees.artists import Artists
    from honeybees.argparse import parser  
    from honeybees.visualization.ModularVisualization import ModularServer
    from honeybees.visualization.modules import ChartModule
    from honeybees.visualization.canvas import Canvas

    class Artists(Artists):
        def __init__(self, model):
            Artists.__init__(self, model)

        def draw_people(self, model, agents, idx):
            return {"type": "shape", "shape": "circle", "r": 1, "filled": True, "color": 'blue'}

    class People(AgentBaseClass):
        def __init__(self, model, agents):
            self.n = 1000
            self.model = model
            self.agents = agents
            self.age = np.random.randint(0, 100, self.n)
            self.locations = np.zeros((self.n, 2), dtype=np.float32)
            self.update_locations()

        def update_locations(self):
            self.locations[:, 0] = np.random.uniform(self.model.xmin, self.model.xmax, self.n)
            self.locations[:, 1] = np.random.uniform(self.model.ymin, self.model.ymax, self.n)

        def step(self):
            self.age += 1
            self.update_locations()

    class Agents:
        def __init__(self, model):
            self.people = People(model, self)

        def step(self):
            self.people.step()

    class ABMModel(Model):
        def __init__(self, config_path, study_area, args=None):
            self.area = Area(self, study_area)
            self.agents = Agents(self)
            self.artists = Artists(self)
            
            current_time = date(2020, 1, 1)
            timestep_length = relativedelta(years=1)
            n_timesteps = 10
            
            Model.__init__(self, current_time, timestep_length, config_path, args=args, n_timesteps=n_timesteps)

            self.reporter = Reporter(self)


    config_path = 'examples/config.yml'
    study_area = {
        'xmin': -10,
        'xmax': 10,
        'ymin': -10,
        'ymax': 10
    }
    model = ABMModel(config_path, study_area)

    if __name__ == '__main__':
        args = parser.parse_args()

        model_params = {
            "config_path": config_path,
            "study_area": study_area,
            "args": args
        }

        if args.headless:
            model = ABMModel(**model_params)
            model.run()
            report = model.report()
        else:
            server_elements = [
                Canvas(
                    study_area['xmin'], study_area['xmax'], study_area['ymin'], study_area['ymax'],
                    max_canvas_height=800, max_canvas_width=1200
                ),
                ChartModule([
                    {"name": "age", "color": "#FF0000"},
                ])
            ]

            DISPLAY_TIMESTEPS = [
                'year',
                'decade'
            ]

            server = ModularServer("Example Model", ABMModel, server_elements, DISPLAY_TIMESTEPS, model_params=model_params, port=None)
            server.launch(port=args.port, browser=args.browser)