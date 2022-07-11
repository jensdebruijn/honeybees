Artists
########

This module is used to draw agents and geographies on the canvas. The :py:class:`honeybees.artists.Artists` can be extended, see :doc:`visualisation`, by adding functions named `draw_{agent_name}` or `draw_{geography_name}`. In addition, the relevant options in the config-file MUST be turned on. An example is given below. Any additional arguments specified in the config-file are also passed on as arguments to the respective function in :py:class:`honeybees.artists.Artists`.

In artists.py:

.. code-block:: python

    class Artists(Artists):
        def __init__(self, model):
            Artists.__init__(self, model)

        def draw_people(self, model, agents, idx):  # agent
            return {"type": "shape", "shape": "circle", "r": 2, "filled": True, "color": 'Red'}

        def draw_rivers(self, color):  # geography
            return {"type": "shape", "shape": "line", "color": color}


in config.yml:

.. code-block:: YAML

    draw:
        draw_agents:
            people:
            draw_every_nth: 1
        draw_geography:
            rivers:
                colors: green
            cities:

The return type of the drawing functions in the :py:class:`honeybees.artists.Artists` must be one of the following:

Point:

.. code-block:: python

    {"type": "shape", "shape": "circle", "r": 1, "filled": True, "color": 'blue'}

Line or multi-line:

.. code-block:: python

    {"type": "shape", "shape": "line", "color": "Blue"}

Polygon or multi-polygon:

.. code-block:: python

    {"type": "shape", "shape": "polygon", "color": "Blue", "filled": True}


It is also possible to update a geography at timesteps. To do so, a function called `update_{geography_name}` must be specified in :py:class:`honeybees.artists.Artists`. This function takes as argument the ID of the geography (as specified in the geojson passed to the model) and the current portrayal of the geography allowing you to update the parameters of the portrayal. For example:

.. code-block:: python

    def update_cities(self, ID, portrayal):
        portrayal['color'] = random.choice(['Green', 'Orange', 'Blue', "Red", 'Purple', 'Pink'])
        return portrayal

.. automodule:: honeybees.artists
    :members: