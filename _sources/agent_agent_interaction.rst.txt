Agent-agent interaction
##########################

The example below shows agent-agent interaction, both between agents of the same type (by infecting others with a virus), and between agents of different types (the government vaccinating people).

.. code-block:: python

    from datetime import date
    import numpy as np
    from dateutil.relativedelta import relativedelta

    from honeybees.model import Model
    from honeybees.area import Area
    from honeybees.reporter import Reporter
    from honeybees.agents import AgentBaseClass
    from honeybees.library.neighbors import find_neighbors

    class People(AgentBaseClass):
        def __init__(self, model, agents):
            self.n = 1000
            self.model = model
            self.agents = agents
            self.age = np.random.randint(0, 100, self.n)
            self.locations = np.zeros((self.n, 2), dtype=np.float32)
            self.set_locations()
            self.infected = np.zeros(self.n, dtype=bool)
            self.infected[0] = True

        def set_locations(self):
            self.locations[:, 0] = np.random.uniform(self.model.xmin, self.model.xmax, self.n)
            self.locations[:, 1] = np.random.uniform(self.model.ymin, self.model.ymax, self.n)

        def spread_virus_to_neighbors(self):
            neighbors = find_neighbors(
                self.locations,
                2,
                3,
                bits=20,
                minx=self.model.xmin,
                miny=self.model.ymin,
                maxx=self.model.xmax,
                maxy=self.model.ymax,
                kind='orthogonal',
                search_ids=np.where(self.infected == True)[0]
            ).ravel()
            neighbors = neighbors[neighbors != -1]
            self.infected[neighbors] = True

        def spread_virus_to_friends(self):
            n_infected_people = self.infected.sum()
            people_to_visit = np.random.choice(np.arange(0, self.n, dtype=np.int32), n_infected_people)
            self.infected[people_to_visit] = True

        def step(self):
            self.age += 1
            self.spread_virus_to_neighbors()
            self.spread_virus_to_friends()

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
        config_path = 'examples/config.yml'
        study_area = {
            'xmin': -10,
            'xmax': 10,
            'ymin': -10,
            'ymax': 10
        }
        model = ABMModel(config_path, study_area)
        for _ in range(10):
            model.step()
            print("Number of infected people", model.agents.people.infected.sum())