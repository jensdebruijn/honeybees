# -*- coding: utf-8 -*-
"""This module is used to report data to the disk and to extract data for visualisation. After initialization of the reporter in the model, the :meth:`honeybees.report.Reporter.step` method is called every timestep, which can obtain data from the agents, and report to disk or save the data for visualiation or writing to disk once the model is finished. The variables to be reported can be configured in the config file. All data is saved to the report folder by default.

In the configuration file you can specify which data should be reported. In this file you can configure which data should be saved from the model in the `report` folder. This should be formatted as follows:

 - **report**:
    - **name**: name of the folder to which the data is saved.
        - **type**: agent type e.g., farmer. Should be identical to attribute name in Agents class.
        - **function**: whether to use a function to parse the data. 'null' means the data is saved literally, 'mean' takes the mean etc. Options are sum/mean.
        - **varname**: attribute name of variable in agent class.
        - **format**: format to save to. Can be 'csv' to save to csv-file per timestep, or 'npy' to save in NumPy binary format.
        - **initial_only**: if true only save the data for the first timestep.
        - **save**: save variable in model run, or export, or both (save/save+export/export).
    - **name2**:
        - ...
        - ...
    - **...**:
        - ...
        - ...
"""
import sys
from collections.abc import Iterable
import os
import numpy as np
try:
    import cupy as cp
except (ModuleNotFoundError, ImportError):
    pass
import pandas as pd
from numba import njit
from math import isinf
from copy import deepcopy
from typing import DefaultDict, Union, Any

class Reporter:
    """This class is used to report data to disk or for visualisation. The `step` method is called each timestep from the model.
    
    Args:
        model: The model.
        subfolder: Optional name of the subfolder to be reported in. By default the report folder from the configuration file is used (general:report_folder).
    """
    def __init__(self, model, subfolder: Union[None, str]=None) -> None:
        self.model = model
        if not hasattr(self.model, 'agents'):  # ensure agents exist
            raise NameError("Attribute agents of model does not exists. This most likely means that the reporter was created before the agents.")
        
        self.variables = {}
        self.timesteps = []

        self.export_folder = self.model.config['general']['report_folder']
        if subfolder:
            self.export_folder = os.path.join(self.export_folder, subfolder)
        self.maybe_create_export_folder()
        
        self.step()

    def maybe_create_export_folder(self) -> None:
        """If required, create folder export folder"""
        try:
            os.makedirs(self.export_folder)
        except OSError:
            pass

    def check_value(self, value: Any):
        """Check whether the value is a Python integer or float, and is not infinite.
        
        Args:
            value: The value to be checked.
        """
        if not (isinstance(value, (int, float)) or value is None):  # check item is normal Python float or int. This is required to succesfully convert to JSON.
            raise ValueError(f"value {value} of type {type(value)} is not Python float or int")
        if isinstance(value, float):
            assert not isinf(value)

    def export_value(self, name: str, value: np.ndarray, conf: dict) -> None:
        """Exports an array of values to the export folder.
        
        Args:
            name: Name of the value to be exported.
            value: The array itself.
            conf: Configuration for saving the file. Contains options such a file format, and whether to export the array in this timestep at all.
        """
        folder = os.path.join(self.export_folder, name)
        try:
            os.makedirs(folder)
        except OSError:
            pass
        if 'format' not in conf:
            raise ValueError(f"Export format must be specified for {name} in config file (npy/csv/xlsx).")
        if 'frequency' in conf and conf['frequency'] == 'initial_only':
            fn = 'initial'
        else:
            fn = f"{self.timesteps[-1].isoformat().replace('-', '').replace(':', '')}"
        if conf['format'] == 'npy':
            fn += '.npy'
            fp = os.path.join(folder, fn)
            np.save(fp, value)
        elif conf['format'] == 'csv':
            fn += '.csv'
            fp = os.path.join(folder, fn)
            if isinstance(value, (np.ndarray, cp.ndarray)):
                value = value.tolist()
            if len(value) > 100_000:
                self.model.logger.info(f"Exporting {len(value)} items to csv. This might take a long time and take a lot of space. Consider using NumPy binary format (npy).")
            with open(fp, 'w') as f:
                f.write("\n".join([str(v) for v in value]))
        else:
            raise ValueError(f"{conf['format']} not recognized")

    def report_value(self, name: Union[str, tuple[str, Any]], value: Any, conf: dict) -> None:
        """This method is used to save and/or export model values.

        Args:
            name: Name of the value to be exported.
            value: The array itself.
            conf: Configuration for saving the file. Contains options such a file format, and whether to export the data or save the data in the model.
        """
        # check if value is of numpy type and check if size is 1. If so, convert to native python type.
        if isinstance(value, (np.ndarray, np.generic, cp.ndarray, cp.generic) if 'cupy' in sys.modules else (np.ndarray, np.generic)):
            if value.size == 1:
                value = value.item()
                self.check_value(value)
        if isinstance(value, list):
            value = [v.item() for v in value]
            for v in value:
                self.check_value(v)
        
        if 'save' not in conf:
            raise ValueError(f"Save type must be specified for {name} in config file (save/save+export/export).")
        if conf['save'] not in ('save', 'export', 'save+export'):
            raise ValueError(f"Save type for {name} in config file must be 'save', 'save+export' or 'export').")
        
        if conf['save'] == 'export' or conf['save'] == 'save+export':
            if 'initial_only' in conf and conf['initial_only']:
                if self.model.current_timestep == 0:
                    self.export_value(name, value, conf)
            else:
                self.export_value(name, value, conf)

        if conf['save'] == 'save' or conf['save'] == 'save+export':
            try:
                if isinstance(name, tuple):
                    name, ID = name
                    if name not in self.variables:
                        self.variables[name] = {}
                    if ID not in self.variables[name]:
                        self.variables[name][ID] = []
                    self.variables[name][ID].append(value)
                else:
                    if name not in self.variables:
                        self.variables[name] = []
                    self.variables[name].append(value)
            except KeyError:
                raise KeyError(f"Variable {name} not initialized. This likely means that an agent is reporting for a group that was not is not the reporter")

    @staticmethod
    @njit
    def mean_per_ID(values: np.ndarray, group_ids: np.ndarray, n_groups: int) -> np.ndarray:
        """Calculates the mean value per group.

        Args:
            values: Numpy array of values.
            group_ids: Group IDs for each value. Must be same size as values.
            n_groups: The total number of groups.

        Returns:
            mean_per_ID: The mean value for each of the groups.
        """
        assert values.size == group_ids.size
        size = values.size
        count_per_group = np.zeros(n_groups, dtype=np.int32)
        sum_per_group = np.zeros(n_groups, dtype=values.dtype)
        for i in range(size):
            group_id = group_ids[i]
            assert group_id < n_groups
            count_per_group[group_id] += 1
            sum_per_group[group_id] += values[i]
        return sum_per_group / count_per_group

    @staticmethod
    @njit
    def sum_per_ID(values: np.ndarray, group_ids: np.ndarray, n_groups: int) -> np.ndarray:
        """Calculates the sum value per group.

        Args:
            values: Numpy array of values.
            group_ids: Group IDs for each value. Must be same size as values.
            n_groups: The total number of groups.

        Returns:
            sum_per_ID: The sum value for each of the groups.
        """
        assert values.size == group_ids.size
        size = values.size
        sum_per_group = np.zeros(n_groups, dtype=values.dtype)
        for i in range(size):
            group_id = group_ids[i]
            assert group_id < n_groups
            sum_per_group[group_id] += values[i]
        return sum_per_group

    def parse_agent_data(self, name: str, values: Any, agents, conf: dict) -> None:
        """This method is used to apply the relevant function to the given data.
        
        Args:
            name: Name of the data to report.
            values: Numpy array of values.
            agents: The relevant agent class.
            conf: Dictionary with report configuration for values.
        """
        function = conf['function']
        if function is None:
            values = deepcopy(values)  # need to copy item, because values are passed without applying any a function.
            self.report_value(name, values, conf)
        else:
            if 'ids' in conf:
                group_ids = getattr(agents, conf['scale'])
                n_groups = conf['ids'].size
                if callable(function):
                    fn = function
                elif function == 'mean':
                    fn = self.mean_per_ID
                elif function == 'sum':
                    fn = self.sum_per_ID
                else:
                    raise ValueError(f'{function} function unknown')
                self.report_value(name, fn(values, group_ids, n_groups), conf)
            else:
                if callable(function):
                    fn = function
                elif function == 'mean':
                    fn = np.mean
                elif function == 'sum':
                    fn = np.sum
                else:
                    raise ValueError(f'{function} function unknown')
                self.report_value(name, fn(getattr(agents, conf['varname'])), conf)

    def extract_agent_data(self, name: str, conf: dict) -> None:
        """This method is used to extract agent data and apply the relevant function to the given data.
        
        Args:
            name: Name of the data to report.
            conf: Dictionary with report configuration for values.
        """
        agents = getattr(self.model.agents, conf['type'])
        try:
            values = getattr(agents, conf['varname'])
        except AttributeError:
            raise AttributeError(f"Trying to export '{conf['varname']}', but no such attribute exists for agent type '{conf['type']}'")
        if 'split' in conf and conf['split']:
            for ID, admin_values in zip(agents.ids, values):
                self.parse_agent_data((name, ID), admin_values, agents, conf)
        else:
            self.parse_agent_data(name, values, agents, conf)

    def step(self) -> None:
        """This method is called every timestep. First appends the current model time to the list of times for the reporter. Then iterates through the data to be reported on and calls the extract_agent_data method for each of them."""
        self.timesteps.append(self.model.current_time)
        if self.model.config is not None and 'report' in self.model.config:
            for name, conf in self.model.config['report'].items():
                self.extract_agent_data(name, conf)

    def report(self) -> dict:
        """This method can be called to save the data that is currently saved in memory to disk."""
        report_dict = {}
        for name, values in self.variables.items():
            if isinstance(values, dict):
                df = pd.DataFrame.from_dict(values)
                df.index = self.timesteps
            elif isinstance(values[0], Iterable):
                df = pd.DataFrame.from_dict(
                    {
                        k: v
                        for k, v in zip(self.timesteps, values)
                    }
                )
            else:
                df = pd.DataFrame(values, index=self.timesteps, columns=[name])
            if 'format' not in self.model.config['report'][name]:
                raise ValueError(f"Key 'format' not specified in config file for {name}")
            export_format = self.model.config['report'][name]['format']
            filepath = os.path.join(self.export_folder, name + '.' + export_format)
            if export_format == 'csv':
                df.to_csv(filepath)
            elif export_format == 'xlsx':
                df.to_excel(filepath)
            elif export_format == 'npy':
                np.save(filepath, df.values)
            else:
                raise ValueError(f'save_to format {export_format} unknown')
        return report_dict
