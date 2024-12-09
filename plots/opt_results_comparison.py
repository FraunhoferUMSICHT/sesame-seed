# more generic approach to plot comparison of model variants

import os
import pandas as pd
import matplotlib.pyplot as plt

import sys

plotstyle_path = os.path.realpath(os.path.join(os.getcwd(), "plots"))
sys.path.append(plotstyle_path)

from plotstyles import Plotstyles

style_inst = Plotstyles()
style_inst.set_pub()


def create_result_df(storage_type):
    # initialize results DataFrame
    res_data = pd.DataFrame()

    # path to optimization results
    folder_path = os.path.realpath(os.path.join(os.getcwd(), "src", "results"))

    # collect all data of selected storage type
    folders = [f for f in os.listdir(folder_path) if storage_type in f]

    for f in folders:
        data_path = os.path.join(folder_path, f)

        # collect all result files
        csv_files = [
            os.path.join(data_path, f)
            for f in os.listdir(data_path)
            if os.path.isfile(os.path.join(data_path, f))
        ]

        # collect results file of most recent run
        file = max(csv_files, key=os.path.getmtime)

        # read data from csv file
        data = pd.read_csv(file, sep=";")
        # filter active scenarios
        data = data[data["active"] > 0]

        # automatically read method

        for i in data.index:
            # detect weather storage losses are considered from folder name
            if "with_" in f:
                if "constant" in f:
                    data.loc[i, "storage losses"] = "constant"
                elif "soc_dep" in f:
                    data.loc[i, "storage losses"] = "soc dependant"
            elif "without" in f:
                data.loc[i, "storage losses"] = "without"
            else:
                data.loc[i, "storage losses"] = "unknown"
                print(
                    "It can not be inferred from the folder name if storage losses are considered!"
                )

            # detect method of storage losses from scenario name
            if data.loc[i, "storage losses"] == "constant":
                method = "".join(data.loc[i, "name"].split("_")[-1])
                data.loc[i, "storage losses method"] = method
            elif data.loc[i, "storage losses"] == "soc dependant":
                method = " ".join(data.loc[i, "name"].split("_")[-2:])
                data.loc[i, "storage losses method"] = method
            elif data.loc[i, "storage losses"] == "without":
                data.loc[i, "storage losses method"] = None
            else:
                print(
                    "method of storage loss implementation can not be inferred from scenario name!"
                )
                data.loc[i, "storage losses method"] = None

            # detect optimization method from folder name
            if "sos2" in f:
                data.loc[i, "efficiency"] = "SOS2"
            elif "bigm" in f or "big_m" in f:
                data.loc[i, "efficiency"] = "BigM"
            elif "linear" in f:
                data.loc[i, "efficiency"] = "linear"
            else:
                print(
                    "method of efficiency implementation can not be inferred from folder name!"
                )
                data.loc[i, "efficiency method"] = "unknown"

            # detect method of efficiency from scenario name
            if data.loc[i, "efficiency"] == "SOS2":
                method = " ".join(data.loc[i, "name"].split("_")[2:4])
                data.loc[i, "efficiency method"] = method
            elif data.loc[i, "efficiency"] == "BigM":
                method = " ".join(data.loc[i, "name"].split("_")[2:4])
                data.loc[i, "efficiency method"] = method
            elif data.loc[i, "efficiency"] == "linear":
                method = "".join(data.loc[i, "name"].split("_")[-2:-1])
                data.loc[i, "efficiency method"] = method
            else:
                print(
                    "method of efficiency implementation can not be inferred from scenario name!"
                )
                data.loc[i, "efficiency method"] = None

            # detect season
            if "sommer" in data.loc[i, "name"]:
                data.loc[i, "season"] = "summer"
            elif "winter" in data.loc[i, "name"]:
                data.loc[i, "season"] = "winter"
            else:
                print("season can not be inferred from scenario name!")
                data.loc[i, "season"] = None

        res_data = pd.concat([res_data, data])

    return res_data


def process_subplot_data(
    df, season, df_columns, method_columns, subplot_index, subplot_column, values
):
    # filter complete data for season and select columns to plot
    data_subplot = df[df["season"] == season].loc[:, df_columns]

    data_subplot = data_subplot[data_subplot["efficiency"].isin(method_columns)]
    data_subplot = data_subplot.pivot(
        index=subplot_index, columns=subplot_column, values=values
    )

    return data_subplot


def calculate_deviation_in_percent(processed_subplot_data, run_df, run):
    # initialize return DataFrame
    data_subplot = pd.DataFrame()

    # calculate deviation from specified run
    for i in processed_subplot_data.index:
        for j in processed_subplot_data.columns:
            data_subplot.loc[i, j] = abs(
                100
                * (processed_subplot_data.loc[i, j] - run_df.loc[*run])
                / run_df.loc[*run]
            )

    return data_subplot


def plot_comparison_optimization_results_soltime_phs(values):
    # read and process data from results folder
    data = create_result_df("phs")

    # initialize figure
    fig, ax = plt.subplots(
        2,
        2,
        figsize=(12, 8),
        gridspec_kw={"width_ratios": [4, 1]},
        sharex="col",
        sharey=True,
    )

    # subplot 0,0:
    data_subplot_0_0 = process_subplot_data(
        data,
        "summer",
        ["efficiency", "efficiency method", "solution_time"],
        ["SOS2", "BigM"],
        "efficiency method",
        "efficiency",
        values,
    )

    data_subplot_0_0.plot.bar(ax=ax[0, 0])
    ax[0, 0].set_title("summer")
    ax[0, 0].set_ylabel("solution time [s]")

    # subplot 0,1:
    data_subplot_0_1 = process_subplot_data(
        data,
        "summer",
        ["efficiency", "efficiency method", "solution_time"],
        ["linear"],
        "efficiency",
        "efficiency method",
        values,
    )

    data_subplot_0_1.plot.bar(
        ax=ax[0, 1], width=0.27, color=["#005B7F", "#008598", "#39C1CD"]
    )

    # subplot 1,0:
    data_subplot_1_0 = process_subplot_data(
        data,
        "winter",
        ["efficiency", "efficiency method", "solution_time"],
        ["SOS2", "BigM"],
        "efficiency method",
        "efficiency",
        values,
    )

    data_subplot_1_0.plot.bar(ax=ax[1, 0])
    ax[1, 0].set_title("winter")
    ax[1, 0].set_ylabel("solution time [s]")

    # subplot 1,1:
    data_subplot_1_1 = process_subplot_data(
        data,
        "winter",
        ["efficiency", "efficiency method", "solution_time"],
        ["linear"],
        "efficiency",
        "efficiency method",
        values,
    )

    data_subplot_1_1.plot.bar(
        ax=ax[1, 1], width=0.27, color=["#005B7F", "#008598", "#39C1CD"]
    )

    for row in ax:
        for a in row:
            a.grid(axis="y")
            a.set_xlabel(" ")
            a.set_yscale("log")

    handles1, labels1 = ax[1, 0].get_legend_handles_labels()
    handles2, labels2 = ax[1, 1].get_legend_handles_labels()

    handles = handles1 + handles2
    labels = labels1 + labels2

    fig.legend(handles, labels, loc="upper right", ncol=3)

    [[c.get_legend().remove() for c in r] for r in ax]

    plt.tight_layout()
    plt.show()


def plot_comparison_optimization_results_objective_phs(
    comparison_method, comparison_run, values
):
    comp = [comparison_run, comparison_method]

    # read and process data from results folder
    data = create_result_df("phs")

    # initialize figure
    fig, ax = plt.subplots(
        2,
        4,
        figsize=(16, 8),
        gridspec_kw={"width_ratios": [4, 1, 4, 1]},
        sharex="col",
        sharey="row",
    )

    # subplot 0,0:
    # compare non constant efficiency method implementations for summer
    data_subplot_0_0 = process_subplot_data(
        data,
        "summer",
        ["efficiency", "efficiency method", "objective"],
        ["SOS2", "BigM"],
        "efficiency method",
        "efficiency",
        values,
    )

    data_subplot_0_0.plot.bar(ax=ax[0, 0])

    ax[0, 0].set_title("summer")
    ax[0, 0].set_ylabel("objective [-]")

    # subplot 0,1:
    # compare constant efficiency method implementations for summer
    data_subplot_0_1 = process_subplot_data(
        data,
        "summer",
        ["efficiency", "efficiency method", "objective"],
        ["linear"],
        "efficiency",
        "efficiency method",
        values,
    )

    data_subplot_0_1.plot.bar(
        ax=ax[0, 1], width=0.27, color=["#005B7F", "#008598", "#39C1CD"]
    )

    # deviation plots summer
    if comparison_method in ["SOS2", "BigM"]:
        comp_data = data_subplot_0_0
    elif comparison_method in ["max", "mean", "reg"]:
        comp_data = data_subplot_0_1

    # subplot 1,0:
    # compare deviation from specified run
    data_subplot_1_0 = calculate_deviation_in_percent(data_subplot_0_0, comp_data, comp)

    data_subplot_1_0.plot.bar(ax=ax[1, 0])
    ax[1, 0].set_ylabel(
        "deviation to " + comparison_method + "-" + comparison_run + " [%]"
    )
    ax[1, 0].set_yscale("log")

    # subplot 1,1:
    # compare deviation from specified run
    data_subplot_1_1 = calculate_deviation_in_percent(data_subplot_0_1, comp_data, comp)

    data_subplot_1_1.plot.bar(
        ax=ax[1, 1], width=0.27, color=["#005B7F", "#008598", "#39C1CD"]
    )

    # subplot 0,2:
    # compare non constant efficiency method implementations for winter
    data_subplot_0_2 = process_subplot_data(
        data,
        "winter",
        ["efficiency", "efficiency method", "objective"],
        ["SOS2", "BigM"],
        "efficiency method",
        "efficiency",
        values,
    )

    data_subplot_0_2.plot.bar(ax=ax[0, 2])

    ax[0, 2].set_title("winter")

    # subplot 0,3:
    # compare constant efficiency method implementations for winter
    data_subplot_0_3 = process_subplot_data(
        data,
        "winter",
        ["efficiency", "efficiency method", "objective"],
        ["linear"],
        "efficiency",
        "efficiency method",
        values,
    )

    data_subplot_0_3.plot.bar(
        ax=ax[0, 3], width=0.27, color=["#005B7F", "#008598", "#39C1CD"]
    )

    # deviation plots for winter
    if comparison_method in ["SOS2", "BigM"]:
        comp_data = data_subplot_0_2
    elif comparison_method in ["max", "mean", "reg"]:
        comp_data = data_subplot_0_3

    # subplot 1,2:
    # compare deviation from specified run
    data_subplot_1_2 = calculate_deviation_in_percent(data_subplot_0_2, comp_data, comp)

    data_subplot_1_2.plot.bar(ax=ax[1, 2])

    # subplot 1,3:
    # compare deviation from specified run
    data_subplot_1_3 = calculate_deviation_in_percent(data_subplot_0_3, comp_data, comp)

    data_subplot_1_3.plot.bar(
        ax=ax[1, 3], width=0.27, color=["#005B7F", "#008598", "#39C1CD"]
    )

    for row in ax:
        for a in row:
            a.grid(axis="y")
            a.set_xlabel(" ")

    handles1, labels1 = ax[1, 0].get_legend_handles_labels()
    handles2, labels2 = ax[1, 1].get_legend_handles_labels()

    handles = handles1 + handles2
    labels = labels1 + labels2

    fig.legend(handles, labels, loc="upper center", ncol=3)

    [[c.get_legend().remove() for c in r] for r in ax]

    plt.tight_layout()
    plt.show()


def plot_comparison_optimization_results_phs(type, comparison_method, comparison_run):
    if type == "objective":
        plot_comparison_optimization_results_objective_phs(
            comparison_method, comparison_run, "objective"
        )
    if type == "solution_time":
        plot_comparison_optimization_results_soltime_phs("solution_time")



def process_subplot_data_caes(
    df, season, loss_type, df_columns, subplot_index, subplot_column, values
):
    # filter complete data for season and select columns to plot
    data_subplot = df[
        (df["season"] == season) & (df["storage losses"] == loss_type)
    ].loc[:, df_columns]

    # data_subplot = data_subplot[data_subplot["storage losses"].isin(losses)]
    data_subplot = (
        data_subplot.groupby(["storage losses method", "efficiency method"])
        .mean()
        .reset_index()
    )
    data_subplot = data_subplot.pivot(
        index=subplot_index, columns=subplot_column, values=values
    )

    data_subplot = data_subplot.transpose()

    return data_subplot


def plot_comparison_optimization_results_objective_caes(
    comparison_method, comparison_run, values
):
    comp = [comparison_run, comparison_method]

    # read and process data from results folder
    data = create_result_df("caes")

    # initialize figure
    fig, ax = plt.subplots(
        2,
        4,
        figsize=(16, 9),
        gridspec_kw={"width_ratios": [4, 1, 4, 1]},
        sharex="col",
        sharey="row",
    )

    # subplot 0,0:
    data_subplot_0_0 = process_subplot_data_caes(
        data,
        "summer",
        "constant",
        ["storage losses method", "efficiency method", "objective"],
        "storage losses method",
        "efficiency method",
        values,
    )

    data_subplot_0_0.plot.bar(ax=ax[0, 0])

    ax[0, 0].set_title("summer")
    ax[0, 0].set_ylabel("objective [-]")

    # subplot 0,1:
    data_subplot_0_1 = process_subplot_data_caes(
        data,
        "summer",
        "soc dependant",
        ["storage losses method", "efficiency method", "objective"],
        "storage losses method",
        "efficiency method",
        values,
    )

    data_subplot_0_1.plot.bar(
        ax=ax[0, 1], width=0.26, color=["#008598", "#39C1CD", "#B2D235"]
    )

    # plot deviation summer
    if comparison_method in ["max", "mean", "reg"]:
        comp_data = data_subplot_0_0
    elif comparison_method in ["2 segments", "3 segments", "4 segments"]:
        comp_data = data_subplot_0_1

    # subplot 1,0:
    # compare deviation from specified run

    data_subplot_1_0 = calculate_deviation_in_percent(data_subplot_0_0, comp_data, comp)

    data_subplot_1_0.plot.bar(ax=ax[1, 0])
    ax[1, 0].set_ylabel(
        "deviation to " + comparison_method + "-" + comparison_run + " [%]"
    )
    # ax[1, 0].set_yscale("log")

    # subplot 1,1:
    # compare deviation from specified run
    data_subplot_1_1 = calculate_deviation_in_percent(data_subplot_0_1, comp_data, comp)

    data_subplot_1_1.plot.bar(
        ax=ax[1, 1], width=0.27, color=["#008598", "#39C1CD", "#B2D235"]
    )

    # subplot 0,2
    data_subplot_0_2 = process_subplot_data_caes(
        data,
        "winter",
        "constant",
        ["storage losses method", "efficiency method", "objective"],
        "storage losses method",
        "efficiency method",
        values,
    )

    data_subplot_0_2.plot.bar(ax=ax[0, 2])
    ax[0, 2].set_title("winter")

    # subplot 0,3:
    data_subplot_0_3 = process_subplot_data_caes(
        data,
        "winter",
        "soc dependant",
        ["storage losses method", "efficiency method", "objective"],
        "storage losses method",
        "efficiency method",
        values,
    )

    data_subplot_0_3.plot.bar(
        ax=ax[0, 3], width=0.27, color=["#008598", "#39C1CD", "#B2D235"]
    )

    # plot deviation winter
    if comparison_method in ["max", "mean", "reg"]:
        comp_data = data_subplot_0_2
    elif comparison_method in ["2 segments", "3 segments", "4 segments"]:
        comp_data = data_subplot_0_3

    # subplot 1,2:
    # compare deviation from specified run

    data_subplot_1_2 = calculate_deviation_in_percent(data_subplot_0_2, comp_data, comp)

    data_subplot_1_2.plot.bar(ax=ax[1, 2])

    # subplot 1,3:
    # compare deviation from specified run
    data_subplot_1_3 = calculate_deviation_in_percent(data_subplot_0_3, comp_data, comp)

    data_subplot_1_3.plot.bar(
        ax=ax[1, 3], width=0.27, color=["#008598", "#39C1CD", "#B2D235"]
    )

    for row in ax:
        for a in row:
            a.grid(axis="y")
            a.set_xlabel("efficiency method")

    handles1, labels1 = ax[1, 0].get_legend_handles_labels()
    handles2, labels2 = ax[1, 1].get_legend_handles_labels()

    handles = handles1 + handles2
    labels = labels1 + labels2

    fig.legend(
        handles, labels, loc="upper center", ncol=3, title="storage losses method"
    )

    [[c.get_legend().remove() for c in r] for r in ax]

    plt.tight_layout()

    plt.show()


def plot_comparison_optimization_results_soltime_caes(values):
    # read and process data from results folder
    data = create_result_df("caes")

    # initialize figure
    fig, ax = plt.subplots(
        2,
        2,
        figsize=(12, 8),
        gridspec_kw={"width_ratios": [4, 1]},
        sharex="col",
        sharey=True,
    )

    # subplot 0,0:
    data_subplot_0_0 = process_subplot_data_caes(
        data,
        "summer",
        "constant",
        ["storage losses method", "efficiency method", "solution_time"],
        "storage losses method",
        "efficiency method",
        values,
    )

    data_subplot_0_0.plot.bar(ax=ax[0, 0])
    ax[0, 0].set_title("summer")
    ax[0, 0].set_ylabel("solution time [s]")

    # subplot 0,1:
    data_subplot_0_1 = process_subplot_data_caes(
        data,
        "summer",
        "soc dependant",
        ["storage losses method", "efficiency method", "solution_time"],
        "storage losses method",
        "efficiency method",
        values,
    )

    data_subplot_0_1.plot.bar(
        ax=ax[0, 1], width=0.26, color=["#008598", "#39C1CD", "#B2D235"]
    )

    # subplot 1,0:
    data_subplot_1_0 = process_subplot_data_caes(
        data,
        "winter",
        "constant",
        ["storage losses method", "efficiency method", "solution_time"],
        "storage losses method",
        "efficiency method",
        values,
    )

    data_subplot_1_0.plot.bar(ax=ax[1, 0])
    ax[1, 0].set_title("winter")
    ax[1, 0].set_ylabel("solution time [s]")

    # subplot 1,1:
    data_subplot_1_1 = process_subplot_data_caes(
        data,
        "winter",
        "soc dependant",
        ["storage losses method", "efficiency method", "solution_time"],
        "storage losses method",
        "efficiency method",
        values,
    )

    data_subplot_1_1.plot.bar(
        ax=ax[1, 1], width=0.26, color=["#008598", "#39C1CD", "#B2D235"]
    )

    for row in ax:
        for a in row:
            a.grid(axis="y")
            a.set_xlabel("efficiency method")
            a.set_yscale("log")

    handles1, labels1 = ax[1, 0].get_legend_handles_labels()
    handles2, labels2 = ax[1, 1].get_legend_handles_labels()

    handles = handles1 + handles2
    labels = labels1 + labels2

    fig.legend(
        handles, labels, loc="upper right", ncol=3, title="storage losses method"
    )

    [[c.get_legend().remove() for c in r] for r in ax]

    plt.tight_layout()
    plt.show()


def plot_comparison_optimization_results_caes(type, comparison_method, comparison_run):
    if type == "objective":
        plot_comparison_optimization_results_objective_caes(
            comparison_method, comparison_run, "objective"
        )
    if type == "solution time":
        plot_comparison_optimization_results_soltime_caes("solution_time")


# type = "objective"
# storage_losses_method = "reg"
# efficiency_method = "2 segments"

# plot_comparison_optimization_results_caes(
#     type, storage_losses_method, efficiency_method
# )
