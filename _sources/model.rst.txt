Model
#########

A Honeybees model consists of a model class, which contains an agent class, area class, and reporter class. The area class defines the study area through its bounds (xmin, xmax, ymin, ymax), and contains any additional features to be displayed, such as rivers.

The agent class is, of course, the hearth of the model. This class is initialized from the model itself, and itself contains all agent classes. In the example below the agent class is initialized as :code:`self.agents = Agents(self)`. Then, in the agent class the people class is initialized through :code:`self.people = People(model, self)`. Any additional agent classes could be initialized for example using :code:`self.government = Government(model, self)`. By passing the agent class (that contains all agent types) to the specific agent type by passing :code:`self`, the agents can also interact with each other (see example in :doc:`introduction`).

Then, the current time (start time), timestep and number of timesteps are set. Then, the reporter is initialized. This class is used to report agent data to disk, and can be configured in the specified config file (`examples/config.yml` in this example). See :doc:`reporting` for more details.

.. code-block:: python

    from datetime import date
    from dateutil.relativedelta import relativedelta

    from honeybees.model import Model
    from honeybees.area import Area
    from honeybees.reporter import Reporter
    from honeybees.agents import AgentBaseClass

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
            
            current_time = date(2020, 1, 1)
            timestep_length = relativedelta(years=1)
            n_timesteps = 10
            
            Model.__init__(self, current_time, timestep_length, config_path, args=args, n_timesteps=n_timesteps)

            self.reporter = Reporter(self)


    config_path = None
    study_area = {
        'name': 'TestArea',
        'xmin': -10,
        'xmax': 10,
        'ymin': -10,
        'ymax': 10
    }
    model = ABMModel(config_path, study_area)

The model can then be run by stepping through the model:

.. code-block:: python

    for i in range(10):
        model.step()

Or by performing all timesteps at once by calling the :code:`run` method:

.. code-block:: python

    model.run()