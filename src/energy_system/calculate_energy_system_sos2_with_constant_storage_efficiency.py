import os
import datetime
import sys

import pandas as pd

import oemof.solph as solph
from oemof.solph import processing, views
from pyomo.opt import SolverStatus, TerminationCondition

# ignore warning concerning missing inputs/outputs of Transformer
import warnings
from oemof.tools.debugging import SuspiciousUsageWarning

warnings.filterwarnings("ignore", category=SuspiciousUsageWarning)

model_path = os.path.realpath(os.path.join(__file__, "..", "..", "storage_models"))
sys.path.append(model_path)

from sos2_storage_with_constant_storage_efficiency import Storage as Stor


def read_scenario_file(scenario_file):
    # import scenario description file
    scenario_options = pd.read_csv(scenario_file, index_col=0, sep=";")

    # initalise scenario status dataframe
    scenario_status = pd.DataFrame(
        index=scenario_options.index,
        data={
            "active": scenario_options.loc[:, "active"],
            "solved": 0,
            "solve_timeout": scenario_options.loc[:, "solve_timeout"],
            "mip_gap": scenario_options.loc[:, "mip_gap"],
            "final_mip_gap": "",
            "solution_time": "",
        },
    )

    return scenario_options, scenario_status


def define_timesteps(scenario_options, i_scenario):
    timeseries_length = scenario_options.at[i_scenario, "timeseries_length"]
    timesteps = pd.date_range(
        scenario_options.at[i_scenario, "start_date"],
        periods=timeseries_length,
        freq=scenario_options.at[i_scenario, "frequency"],
    )

    return timesteps


def read_scenario_parameters(scenario_options, i_scenario):
    # create log message
    log_msg = "[{0:s}]\tCalculating scenario: '{1:s}'\n".format(
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), i_scenario
    )
    # print log message
    print(log_msg, end="")

    # read scenario technology parameters
    P_MAX_IN = scenario_options.at[i_scenario, "P_MAX_IN_[MW]"]
    P_MAX_OUT = scenario_options.at[i_scenario, "P_MAX_OUT_[MW]"]
    P_MIN_IN = scenario_options.at[i_scenario, "P_MIN_IN_[-]"]
    P_MIN_OUT = scenario_options.at[i_scenario, "P_MIN_OUT_[-]"]
    SOC_MIN = scenario_options.at[i_scenario, "SOC_MIN_[MWh]"]
    SOC_MAX = scenario_options.at[i_scenario, "SOC_MAX_[MWh]"]
    SOC_INI = scenario_options.at[i_scenario, "SOC_INI_[-]"]
    ETA_SOC = scenario_options.at[i_scenario, "ETA_SOC_[-]"]

    p_in_breakpoints = [
        float(x)
        for x in scenario_options.at[i_scenario, "p_in_breakpoints_[-]"].split(", ")
    ]
    p_in_stor_breakpoints = [
        float(x)
        for x in scenario_options.at[i_scenario, "p_in_stor_breakpoints_[-]"].split(
            ", "
        )
    ]

    p_out_stor_breakpoints = [
        float(x)
        for x in scenario_options.at[i_scenario, "p_out_stor_breakpoints_[-]"].split(
            ", "
        )
    ]
    p_out_breakpoints = [
        float(x)
        for x in scenario_options.at[i_scenario, "p_out_breakpoints_[-]"].split(", ")
    ]

    sf_dem = scenario_options.at[i_scenario, "sf_dem_[-]"]
    sf_res = scenario_options.at[i_scenario, "sf_res_[-]"]

    return (
        P_MAX_IN,
        P_MAX_OUT,
        P_MIN_IN,
        P_MIN_OUT,
        SOC_MIN,
        SOC_MAX,
        SOC_INI,
        ETA_SOC,
        p_in_breakpoints,
        p_in_stor_breakpoints,
        p_out_breakpoints,
        p_out_stor_breakpoints,
        sf_dem,
        sf_res,
    )


def read_timeseries(scenario_options, i_scenario, sf_dem, sf_res):
    # set path to timeseries data file
    data_path = os.path.realpath(
        os.path.join("data", scenario_options.at[i_scenario, "input_data"])
    )

    # import timeseries data as Series
    demand = (
        sf_dem
        * pd.read_csv(data_path, index_col=0, parse_dates=[0], sep=";").loc[
            :, "demand_[MW]"
        ]
    )

    ee_generation = (
        sf_res
        * pd.read_csv(data_path, index_col=0, parse_dates=[0], sep=";").loc[
            :, "ee_generation_[MW]"
        ]
    )

    return demand, ee_generation


def energy_system_model(
    timesteps,
    demand,
    ee_generation,
    P_MAX_IN,
    P_MAX_OUT,
    P_MIN_IN,
    P_MIN_OUT,
    SOC_MIN,
    SOC_MAX,
    SOC_INI,
    ETA_SOC,
    p_in_breakpoints,
    p_in_stor_breakpoints,
    p_out_breakpoints,
    p_out_stor_breakpoints,
):
    # create energy system
    energy_system = solph.EnergySystem(timeindex=timesteps, infer_last_interval=True)

    # add buses
    ####################################################

    bus_gen = solph.Bus(label="bus_gen")
    energy_system.add(bus_gen)

    bus_dem = solph.Bus(label="bus_dem")
    energy_system.add(bus_dem)

    # add generation
    ####################################################

    ee_gen = solph.components.Source(
        label="ee_gen",
        outputs={bus_gen: solph.Flow(fix=ee_generation, nominal_value=1)},
    )
    energy_system.add(ee_gen)

    fossil_gen = solph.components.Source(
        label="fossil_gen", outputs={bus_gen: solph.Flow(variable_costs=100)}
    )
    energy_system.add(fossil_gen)

    # add demand
    ####################################################

    dem = solph.components.Sink(
        label="dem", inputs={bus_dem: solph.Flow(fix=demand, nominal_value=1)}
    )
    energy_system.add(dem)

    cut_off = solph.components.Sink(
        label="cut_off", inputs={bus_gen: solph.Flow(variable_costs=0)}
    )
    energy_system.add(cut_off)

    # connect generation and demand directly
    ####################################################

    connect = solph.components.Transformer(
        label="connect", inputs={bus_gen: solph.Flow()}, outputs={bus_dem: solph.Flow()}
    )
    energy_system.add(connect)

    # add storage
    ####################################################

    storage = Stor(
        label="storage",
        el_inputs={bus_gen: solph.Flow()},
        el_outputs={bus_dem: solph.Flow()},
        P_MAX_IN=P_MAX_IN,
        P_MAX_OUT=P_MAX_OUT,
        P_MIN_IN=P_MIN_IN,
        P_MIN_OUT=P_MIN_OUT,
        SOC_MIN=SOC_MIN,
        SOC_MAX=SOC_MAX,
        SOC_INI=SOC_INI,
        ETA_SOC=ETA_SOC,
        p_in_breakpoints=p_in_breakpoints,
        p_in_stor_breakpoints=p_in_stor_breakpoints,
        p_out_stor_breakpoints=p_out_stor_breakpoints,
        p_out_breakpoints=p_out_breakpoints,
    )
    energy_system.add(storage)

    # create a pyomo optimization problem
    optimisation_model = solph.Model(energy_system)

    return optimisation_model


def set_up_energy_system_model(scenario_options, i_scenario):
    # define set with timesteps for optimization calculation
    timesteps = define_timesteps(scenario_options, i_scenario)

    # read technology data from scenario file
    (
        P_MAX_IN,
        P_MAX_OUT,
        P_MIN_IN,
        P_MIN_OUT,
        SOC_MIN,
        SOC_MAX,
        SOC_INI,
        ETA_SOC,
        p_in_breakpoints,
        p_in_stor_breakpoints,
        p_out_breakpoints,
        p_out_stor_breakpoints,
        sf_dem,
        sf_res,
    ) = read_scenario_parameters(scenario_options, i_scenario)

    # read timeseries data
    demand, ee_generation = read_timeseries(
        scenario_options, i_scenario, sf_dem, sf_res
    )

    # create optimization model
    model = energy_system_model(
        timesteps,
        demand,
        ee_generation,
        P_MAX_IN,
        P_MAX_OUT,
        P_MIN_IN,
        P_MIN_OUT,
        SOC_MIN,
        SOC_MAX,
        SOC_INI,
        ETA_SOC,
        p_in_breakpoints,
        p_in_stor_breakpoints,
        p_out_breakpoints,
        p_out_stor_breakpoints,
    )

    return model


def process_solver_results(
    solver_results, model, scenario_status, i_scenario, export_root
):
    # test success of solve
    if (solver_results.solver.status == SolverStatus.ok) or (
        solver_results.solver.termination_condition
        in [TerminationCondition.optimal, TerminationCondition.maxTimeLimit]
    ):
        # get meta results of solver
        meta_results = processing.meta_results(model)
        objective = meta_results["objective"]
        problem = meta_results["problem"]
        final_mip_gap = abs(problem["Lower bound"] - objective) / objective
        solver_metadata = {}
        solver_metadata = meta_results["solver"]

        # get result dict
        results = processing.results(model)
        result_storage = pd.DataFrame(views.node(results, "storage")["sequences"])

        # round to zero to account for numerical imprecision
        result_storage[result_storage < 0.0000001] = 0

        # calculate efficiency for every timestep
        result_storage["eta_in"] = (
            result_storage[(("storage", "None"), "P_in_stor")]
            / result_storage[(("storage", "None"), "P_in")]
        )
        result_storage["eta_out"] = (
            result_storage[(("storage", "None"), "P_out")]
            / result_storage[(("storage", "None"), "P_out_stor")]
        )

        # make names easier human readable
        result_storage.rename(
            columns={
                (("storage", "None"), "P_in_stor"): "P_in_stor",
                (("storage", "None"), "P_in"): "P_in",
                (("storage", "None"), "P_out"): "P_out",
                (("storage", "None"), "P_out_stor"): "P_out_stor",
                (("storage", "None"), "soc"): "soc",
            },
            inplace=True,
        )

        # get results for individual buses
        result_bus_gen = pd.DataFrame(views.node(results, "bus_gen")["sequences"])

        result_bus_dem = pd.DataFrame(views.node(results, "bus_dem")["sequences"])

        # define results directory
        # set path to directory
        export_dir = os.path.realpath(os.path.join(export_root, i_scenario))
        # create export directory if necessary
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # export data of storage operation
        export_file = os.path.realpath(os.path.join(export_dir, "storage.csv"))

        result_storage.to_csv(
            export_file,
            header=True,
            index=True,
            index_label="datetime",
            sep=";",
            date_format="%Y-%m-%d %H:%M:%S",
        )

        # export data of generation bus
        export_file = os.path.realpath(os.path.join(export_dir, "bus_gen.csv"))

        result_bus_gen.to_csv(
            export_file,
            header=True,
            index=True,
            index_label="datetime",
            sep=";",
            date_format="%Y-%m-%d %H:%M:%S",
        )

        # export data of demand bus
        export_file = os.path.realpath(os.path.join(export_dir, "bus_dem.csv"))

        result_bus_dem.to_csv(
            export_file,
            header=True,
            index=True,
            index_label="datetime",
            sep=";",
            date_format="%Y-%m-%d %H:%M:%S",
        )

        # set scenario status for current scenario
        scenario_status.at[i_scenario, "objective"] = objective
        scenario_status.at[i_scenario, "final_mip_gap"] = final_mip_gap
        scenario_status.at[i_scenario, "eta_in_mean"] = result_storage["eta_in"].mean()
        scenario_status.at[i_scenario, "eta_out_mean"] = result_storage[
            "eta_out"
        ].mean()
        scenario_status.at[i_scenario, "solved"] = 1
        scenario_status.at[i_scenario, "final_mip_gap"] = final_mip_gap
        if not solver_metadata:
            scenario_status.at[i_scenario, "solution_time"] = "timelimit"
        else:
            scenario_status.at[i_scenario, "solution_time"] = solver_metadata[
                "User time"
            ]

    # create log message
    log_msg = "[{0:s}]\tScenario: '{1:s}' finished .\n".format(
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        i_scenario,
    )

    # print log message
    print(log_msg, end="")


def export_scenario_description(export_root, scenario_status):
    version_date = datetime.datetime.now().strftime("%d_%m_%Y__%H_%M")

    # export scenario status
    export_file = os.path.join(
        export_root, "scenario_status_version_" + version_date + ".csv"
    )

    scenario_status.to_csv(export_file, index_label="name", sep=";")

    # create log message
    log_msg = "[{0:s}]\tCalculated all scenarios.\n".format(
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    # print log message
    print(log_msg, end="")
