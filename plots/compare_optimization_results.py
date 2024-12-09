import os
import pandas as pd
import matplotlib.pyplot as plt

import sys

plotstyle_path = os.path.realpath(os.path.join(os.getcwd(), "plots"))
sys.path.append(plotstyle_path)

from plotstyles import Plotstyles

style_inst = Plotstyles()
style_inst.set_pub()

# initialize result DataFrame


def create_result_df(storage_type):
    res_data = pd.DataFrame()

    folder_path = os.path.realpath(os.path.join(os.getcwd(), "src", "results"))

    # collect all data

    folders = [f for f in os.listdir(folder_path) if storage_type in f]
    print(folders)

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

        data = pd.read_csv(file, sep=";")
        data = data[data["active"] > 0]

        for i in data.index:
            # detect method
            if "sos2" in f:
                data.loc[i, "method"] = "SOS2"
            elif "bigm" in f or "big_m" in f:
                data.loc[i, "method"] = "BigM"
            elif "linear" in f:
                data.loc[i, "method"] = "linear"

            # detect method detail
            if "_se" in data.loc[i, "name"]:
                detail = data.loc[i, "name"][data.loc[i, "name"].find("_se") - 4 :]
                detail = "".join([c for c in detail if c.isdigit()]) + " segments"

                data.loc[i, "method detail"] = detail

            elif "eff" in data.loc[i, "name"]:
                detail = data.loc[i, "name"][data.loc[i, "name"].find("_eff") - 4 :]
                detail = detail.replace("_eff", "").replace("_", "")

                data.loc[i, "method detail"] = detail

            # detect season
            if "sommer" in data.loc[i, "name"]:
                data.loc[i, "season"] = "sommer"
            elif "winter" in data.loc[i, "name"]:
                data.loc[i, "season"] = "winter"

        res_data = pd.concat([res_data, data])

    return res_data


def plot_optimization_methods_comparison(storage_type):
    res_data = create_result_df(storage_type)

    fig, ax = plt.subplots(2, 2, figsize=(16, 8), sharex=True, sharey="row")

    # first subplot
    splt1 = res_data[res_data["season"] == "sommer"].loc[
        :, ["method", "method detail", "objective"]
    ]

    temp1 = splt1[splt1["method"].isin(["SOS2", "BigM"])]
    temp1 = temp1.pivot(index="method detail", columns="method", values="objective")

    temp2 = splt1[splt1["method"].isin(["linear"])]
    temp2 = temp2.pivot(index="method", columns="method detail", values="objective")

    splt1 = pd.concat([temp1, temp2])

    splt1.plot.bar(ax=ax[0, 0])
    ax[0, 0].set_title("summer")
    ax[0, 0].set_ylabel("objective [-]")
    ax[0, 0].grid(axis="y")
    ax[0, 0].set_xlabel(" ")

    splt3 = pd.DataFrame()

    for i in splt1.index:
        splt3.loc[i, "BigM"] = (
            splt1.loc[i, "BigM"] - splt1.loc["10 segments", "SOS2"]
        ) / splt1.loc["10 segments", "SOS2"]

        splt3.loc[i, "SOS2"] = (
            splt1.loc[i, "SOS2"] - splt1.loc["10 segments", "SOS2"]
        ) / splt1.loc["10 segments", "SOS2"]

        splt3.loc[i, "max"] = (
            splt1.loc[i, "max"] - splt1.loc["10 segments", "SOS2"]
        ) / splt1.loc["10 segments", "SOS2"]

        splt3.loc[i, "mean"] = (
            splt1.loc[i, "mean"] - splt1.loc["10 segments", "SOS2"]
        ) / splt1.loc["10 segments", "SOS2"]

        splt3.loc[i, "reg"] = (
            splt1.loc[i, "reg"] - splt1.loc["10 segments", "SOS2"]
        ) / splt1.loc["10 segments", "SOS2"]

    splt3.plot.bar(ax=ax[1, 0])
    ax[1, 0].set_ylabel("relative deviation to SOS2 - 10 segments [-]")
    ax[1, 0].grid(axis="y")
    ax[1, 0].set_xlabel(" ")
    ax[1, 0].set_ylim(-0.025, 0.09)

    # second subplot
    splt2 = res_data[res_data["season"] == "winter"].loc[
        :, ["method", "method detail", "objective"]
    ]

    temp1 = splt2[splt2["method"].isin(["SOS2", "BigM"])]
    temp1 = temp1.pivot(index="method detail", columns="method", values="objective")

    temp2 = splt2[splt2["method"].isin(["linear"])]
    temp2 = temp2.pivot(index="method", columns="method detail", values="objective")

    splt2 = pd.concat([temp1, temp2])

    splt2.plot.bar(ax=ax[0, 1])
    ax[0, 1].set_title("winter")
    ax[0, 1].set_ylabel("objective [-]")
    ax[0, 1].grid(axis="y")
    ax[0, 1].set_xlabel(" ")

    splt4 = pd.DataFrame()

    for i in splt2.index:
        splt4.loc[i, "BigM"] = (
            splt2.loc[i, "BigM"] - splt2.loc["10 segments", "SOS2"]
        ) / splt2.loc["10 segments", "SOS2"]

        splt4.loc[i, "SOS2"] = (
            splt2.loc[i, "SOS2"] - splt2.loc["10 segments", "SOS2"]
        ) / splt2.loc["10 segments", "SOS2"]

        splt4.loc[i, "max"] = (
            splt2.loc[i, "max"] - splt2.loc["10 segments", "SOS2"]
        ) / splt2.loc["10 segments", "SOS2"]

        splt4.loc[i, "mean"] = (
            splt2.loc[i, "mean"] - splt2.loc["10 segments", "SOS2"]
        ) / splt2.loc["10 segments", "SOS2"]

        splt4.loc[i, "reg"] = (
            splt2.loc[i, "reg"] - splt2.loc["10 segments", "SOS2"]
        ) / splt2.loc["10 segments", "SOS2"]

    splt4.plot.bar(ax=ax[1, 1])
    ax[1, 1].set_ylabel("relative deviation to SOS2 - 10 segments [-]")
    ax[1, 1].grid(axis="y")
    ax[1, 1].set_xlabel(" ")
    ax[1, 1].set_ylim(-0.025, 0.09)

    handles, labels = ax[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3)

    [[c.get_legend().remove() for c in r] for r in ax]

    plt.tight_layout()
    plt.show()


# ---------------------


def plot_optimization_methods_comparison_different(storage_type):
    res_data = create_result_df(storage_type)

    fig, ax = plt.subplots(
        2,
        4,
        figsize=(16, 8),
        gridspec_kw={"width_ratios": [4, 1, 4, 1]},
        sharex="col",
        sharey="row",
    )

    # first subplot
    splt1 = res_data[res_data["season"] == "sommer"].loc[
        :, ["method", "method detail", "objective"]
    ]

    temp1 = splt1[splt1["method"].isin(["SOS2", "BigM"])]
    temp1 = temp1.pivot(index="method detail", columns="method", values="objective")

    temp2 = splt1[splt1["method"].isin(["linear"])]
    temp2 = temp2.pivot(index="method", columns="method detail", values="objective")

    splt1 = pd.concat([temp1, temp2])

    # splt1.plot.bar(ax=ax[0, 0])
    # ax[0, 0].set_title("summer")
    # ax[0, 0].set_ylabel("objective [-]")
    # ax[0, 0].grid(axis="y")
    # ax[0, 0].set_xlabel(" ")

    temp1.plot.bar(ax=ax[0, 0])
    ax[0, 0].set_title("summer")
    ax[0, 0].set_ylabel("objective [-]")
    ax[0, 0].grid(axis="y")
    ax[0, 0].set_xlabel(" ")

    temp2.plot.bar(ax=ax[0, 1], width=0.27, color=["#005B7F", "#008598", "#39C1CD"])
    # ax[0, 0].set_title("summer")
    ax[0, 1].set_ylabel("objective [-]")
    ax[0, 1].grid(axis="y")
    ax[0, 1].set_xlabel(" ")

    splt3 = pd.DataFrame()

    for i in temp1.index:
        splt3.loc[i, "BigM"] = (
            100
            * (splt1.loc[i, "BigM"] - splt1.loc["10 segments", "SOS2"])
            / splt1.loc["10 segments", "SOS2"]
        )

        splt3.loc[i, "SOS2"] = (
            100
            * (splt1.loc[i, "SOS2"] - splt1.loc["10 segments", "SOS2"])
            / splt1.loc["10 segments", "SOS2"]
        )

    splt3.plot.bar(ax=ax[1, 0])
    ax[1, 0].set_ylabel("relative deviation to SOS2 - 10 segments [%]")
    ax[1, 0].grid(axis="y")
    ax[1, 0].set_xlabel(" ")
    ax[1, 0].set_yscale("log")
    # ax[1, 0].set_ylim(-0.025, 0.09)

    temp3 = pd.DataFrame()

    for i in temp2.index:
        temp3.loc[i, "max"] = (
            100
            * (splt1.loc[i, "max"] - splt1.loc["10 segments", "SOS2"])
            / splt1.loc["10 segments", "SOS2"]
        )

        temp3.loc[i, "mean"] = (
            100
            * (splt1.loc[i, "mean"] - splt1.loc["10 segments", "SOS2"])
            / splt1.loc["10 segments", "SOS2"]
        )

        temp3.loc[i, "reg"] = (
            100
            * (splt1.loc[i, "reg"] - splt1.loc["10 segments", "SOS2"])
            / splt1.loc["10 segments", "SOS2"]
        )

    temp3.plot.bar(ax=ax[1, 1], width=0.27, color=["#005B7F", "#008598", "#39C1CD"])
    ax[1, 1].set_ylabel("relative deviation to SOS2 - 10 segments [%]")
    ax[1, 1].grid(axis="y")
    ax[1, 1].set_xlabel(" ")
    ax[1, 1].set_yscale("log")
    # ax[1, 1].set_ylim(-0.025, 0.09)

    # second subplot
    splt2 = res_data[res_data["season"] == "winter"].loc[
        :, ["method", "method detail", "objective"]
    ]

    temp1 = splt2[splt2["method"].isin(["SOS2", "BigM"])]
    temp1 = temp1.pivot(index="method detail", columns="method", values="objective")

    temp2 = splt2[splt2["method"].isin(["linear"])]
    temp2 = temp2.pivot(index="method", columns="method detail", values="objective")

    splt2 = pd.concat([temp1, temp2])

    temp1.plot.bar(ax=ax[0, 2])
    ax[0, 2].set_title("winter")
    ax[0, 2].set_ylabel("objective [-]")
    ax[0, 2].grid(axis="y")
    ax[0, 2].set_xlabel(" ")

    temp2.plot.bar(ax=ax[0, 3], width=0.27, color=["#005B7F", "#008598", "#39C1CD"])
    ax[0, 3].set_ylabel("objective [-]")
    ax[0, 3].grid(axis="y")
    ax[0, 3].set_xlabel(" ")

    splt4 = pd.DataFrame()

    for i in temp1.index:
        splt4.loc[i, "BigM"] = (
            100
            * (splt2.loc[i, "BigM"] - splt2.loc["10 segments", "SOS2"])
            / splt2.loc["10 segments", "SOS2"]
        )

        splt4.loc[i, "SOS2"] = (
            100
            * (splt2.loc[i, "SOS2"] - splt2.loc["10 segments", "SOS2"])
            / splt2.loc["10 segments", "SOS2"]
        )

    splt4.plot.bar(ax=ax[1, 2])
    ax[1, 2].set_ylabel("relative deviation to SOS2 - 10 segments [%]")
    ax[1, 2].grid(axis="y")
    ax[1, 2].set_xlabel(" ")
    ax[1, 2].set_yscale("log")
    # ax[1, 2].set_ylim(-0.025, 0.09)

    temp3 = pd.DataFrame()

    for i in temp2.index:
        temp3.loc[i, "max"] = (
            100
            * (splt2.loc[i, "max"] - splt2.loc["10 segments", "SOS2"])
            / splt2.loc["10 segments", "SOS2"]
        )

        temp3.loc[i, "mean"] = (
            100
            * (splt2.loc[i, "mean"] - splt2.loc["10 segments", "SOS2"])
            / splt2.loc["10 segments", "SOS2"]
        )

        temp3.loc[i, "reg"] = (
            100
            * (splt2.loc[i, "reg"] - splt2.loc["10 segments", "SOS2"])
            / splt2.loc["10 segments", "SOS2"]
        )

    temp3.plot.bar(ax=ax[1, 3], width=0.27, color=["#005B7F", "#008598", "#39C1CD"])
    ax[1, 3].set_ylabel("relative deviation to SOS2 - 10 segments [%]")
    ax[1, 3].grid(axis="y")
    ax[1, 3].set_xlabel(" ")
    ax[1, 3].set_yscale("log")
    # ax[1, 3].set_ylim(-0.025, 0.09)

    handles1, labels1 = ax[1, 0].get_legend_handles_labels()
    handles2, labels2 = ax[1, 1].get_legend_handles_labels()

    handles = handles1 + handles2
    labels = labels1 + labels2

    fig.legend(handles, labels, loc="upper center", ncol=3)

    [[c.get_legend().remove() for c in r] for r in ax]

    plt.tight_layout()
    plt.show()


# ***********************************


def plot_optimization_soltimes_comparison(storage_type):
    res_data = create_result_df(storage_type)

    fig, ax = plt.subplots(
        2,
        2,
        figsize=(12, 8),
        gridspec_kw={"width_ratios": [4, 1]},
        sharex="col",
    )

    # first subplot
    splt1 = res_data[res_data["season"] == "sommer"].loc[
        :, ["method", "method detail", "solution_time"]
    ]

    temp1 = splt1[splt1["method"].isin(["SOS2", "BigM"])]
    temp1 = temp1.pivot(index="method detail", columns="method", values="solution_time")

    temp2 = splt1[splt1["method"].isin(["linear"])]
    temp2 = temp2.pivot(index="method", columns="method detail", values="solution_time")

    splt1 = pd.concat([temp1, temp2])

    # splt1.plot.bar(ax=ax[0, 0])
    # ax[0, 0].set_title("summer")
    # ax[0, 0].set_ylabel("solution time [s]")
    # ax[0, 0].grid(axis="y")
    # ax[0, 0].set_xlabel(" ")

    temp1.plot.bar(ax=ax[0, 0])
    ax[0, 0].set_title("summer")
    ax[0, 0].set_ylabel("solution time [s]")
    ax[0, 0].grid(axis="y")
    ax[0, 0].set_xlabel(" ")

    temp2.plot.bar(ax=ax[0, 1], width=0.27, color=["#005B7F", "#008598", "#39C1CD"])
    # ax[0, 0].set_title("summer")
    ax[0, 1].set_ylabel("solution time [s]")
    ax[0, 1].grid(axis="y")
    ax[0, 1].set_xlabel(" ")

    # second subplot
    splt2 = res_data[res_data["season"] == "winter"].loc[
        :, ["method", "method detail", "solution_time"]
    ]

    temp1 = splt2[splt2["method"].isin(["SOS2", "BigM"])]
    temp1 = temp1.pivot(index="method detail", columns="method", values="solution_time")

    temp2 = splt2[splt2["method"].isin(["linear"])]
    temp2 = temp2.pivot(index="method", columns="method detail", values="solution_time")

    splt2 = pd.concat([temp1, temp2])

    temp1.plot.bar(ax=ax[1, 0])
    ax[1, 0].set_title("winter")
    ax[1, 0].set_ylabel("solution time [s]")
    ax[1, 0].grid(axis="y")
    ax[1, 0].set_xlabel(" ")

    temp2.plot.bar(ax=ax[1, 1], width=0.27, color=["#005B7F", "#008598", "#39C1CD"])
    ax[1, 1].set_ylabel("solution time [s]")
    ax[1, 1].grid(axis="y")
    ax[1, 1].set_xlabel(" ")

    handles1, labels1 = ax[0, 0].get_legend_handles_labels()
    handles2, labels2 = ax[0, 1].get_legend_handles_labels()

    handles = handles1 + handles2
    labels = labels1 + labels2

    fig.legend(handles, labels, loc="upper right", ncol=3)

    [[c.get_legend().remove() for c in r] for r in ax]

    plt.tight_layout()
    plt.show()


# plot_optimization_soltimes_comparison()
