Introduction
############

Honeybees is a agent-based modelling framework targeted at large-scale agent-based models written in Python. The framework is heavily inpsired by `Mesa <https://github.com/projectmesa/mesa>`_, but the agent class is fully adapted for high-speed and memory efficient agent operations.

Rather than each class instance representing a single agent, each class can represent an (almost) infinite number of agents of the same type, such as farmers, governments or traders. Agent characteristics (and location) are stored in NumPy (or CuPy) arrays, where the first item of each array represents the characteristic of the first agent, the second item for the second agent, and so fort.

.. code-block:: python

    import numpy as np
    from honeybees.agents import AgentBaseClass

    class Agents(AgentBaseClass):
        def __init__(self, model, agents):
            self.n = 10_000_000  # initialize 10 million farmers
            self.income = randint(0, 1000, size=self.n) #  
            self.has_well = randint(0, 2, size=self.n)

Changing the state of an agent based on their characteristics can be done by interacting directly with those arrays. In the following example, all agents with an income above 500, install a well.

.. code-block:: python

    import numpy as np
    from honeybees.agents import AgentBaseClass

    class Agents(AgentBaseClass):
        def __init__(self, model, agents):
            self.n = 10_000_000  # initialize 10 million farmers
            self.income = randint(0, 1000, size=self.n)  
            self.has_well = randint(0, 2, size=self.n)

        def install_well(self):
            self.has_well[self.income > 500] = True

More complicated behavior can be implemented using `Numba <http://numba.pydata.org/>`_, which can be used to compile Python code, and thus is several orders of magnitude faster than normal Python code (almost identical to NumPy speed). However, as Numba-compiled code cannot access class atributes, a helper method can be used. In the example below agent decision-making is exactly the same as above, but using a Numba compiled method.

.. code-block:: python

    import numpy as np
    from honeybees.agents import AgentBaseClass
    from numba import njit

    class Agents(AgentBaseClass):
        def __init__(self, model, agents):
            self.n = 10_000
            self.income = randint(0, 1000, self.n)
            self.has_well = randint(0, 2, self.n)

        @staticmethod
        @njit
        def install_well_numba(n, income, has_well):
            for i in range(n):
                if income[i] > 500:
                    has_well[i] = 1
        
        def install_well(self):
            self.install_well_numba(self.n, self.income, self.has_well)

Multiple agent types
*************************

You can also make multiple agent types. For example, by creating a government. For example, you could create an Agent class that initializes both the Farmers and the Government class. By passing the Agent class to the Government class, the Government class can easily access the farmers. In this example, the government installs a well for every 100th agent every timestep.

.. code-block:: python

    import numpy as np
    from honeybees.agents import AgentBaseClass

    class Farmers(AgentBaseClass):
        def __init__(self, model, agents):
            self.n = 10_000_000  # initialize 10 million farmers
            self.income = randint(0, 1000, size=self.n) #  
            self.has_well = randint(0, 2, size=self.n)

    class Government(AgentBaseClass):
        def __init__(self, model, agents):
            self.model = model
            self.agents = agents

        def step(self):
            self.agents.farmers.has_well[::100] = True

    class Agents:
        def __init__(self, model):
            self.farmers = Farmers(model, self)
            self.government = Government(model, self)

        def step(self):
            self.government.step()
            self.farmers.step()
