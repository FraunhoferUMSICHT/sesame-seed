import os
import pandas as pd
import matplotlib.pyplot as plt

import warnings

# Suppress all UserWarning messages
warnings.filterwarnings("ignore", category=UserWarning)

import sys

plotstyle_path = os.path.realpath(os.path.join(os.getcwd(), "plots"))
sys.path.append(plotstyle_path)

from plotstyles import Plotstyles

style_inst = Plotstyles()
style_inst.set_pub()

# read data

data_path = os.path.realpath(
    os.path.join(os.getcwd(), "schedule_simulation_results", "PHS")
)


def map_kpi_name_ger_en(kpi):
    if kpi == "Average charging efficiency":
        kpi_ger = "mittl. Einspeicherwirkungsgrad [-]"
    elif kpi == "Average discharging efficiency":
        kpi_ger = "mittl. Ausspeicherwirkungsgrad [-]"
    elif kpi == "Charging utilization rate":
        kpi_ger = "Einspeichernutzungsgrad [-]"
    elif kpi == "Discharging utilization rate":
        kpi_ger = "Ausspeichernutzungsgrad [-]"
    elif kpi == "Total charged electrical energy":
        kpi_ger = "Zugeführte el. Energie [MWh]"
    elif kpi == "Total discharged electrical energy":
        kpi_ger = "Erzeugte el. Energie [MWh]"
    elif kpi == "Total charging duration":
        kpi_ger = "Beladungszeit [h]"
    elif kpi == "Total discharging duration":
        kpi_ger = "Entladungszeit [h]"
    else:
        print("the given kpi is not valid")

    return kpi_ger


def create_result_df(kpi, season):
    datafiles = [
        f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))
    ]

    result_df = pd.DataFrame(
        index=[s.replace(".xlsx", "") for s in datafiles],
        columns=["kpi", "simulation", "optimization", "deviation"],
    )

    for f in datafiles:
        if f.endswith(".xlsx"):
            data = (
                pd.read_excel(
                    os.path.join(data_path, f),
                    sheet_name="Kennzahlen",
                    header=0,
                )
            ).iloc[1:11, 1:5]

            data.columns = ["kpi", "simulation", "optimization", "deviation"]

            temp_df = data[data["kpi"] == kpi]
            temp_df.index = [f.replace(".xlsx", "")]

            result_df.loc[f.replace(".xlsx", "")] = temp_df.loc[f.replace(".xlsx", "")]

    df_kpi_season = pd.DataFrame(
        index=["2 segments", "6 segments", "10 segments", "linear"],
        columns=["SOS2", "BigM", "linear reg"],
    )

    for i in df_kpi_season.index:
        s = "".join([c for c in str(i) if c.isdigit()]) + "Seg"

        if s == "Seg":
            df_kpi_season.loc[i, "linear reg"] = (
                result_df["deviation"][
                    result_df.index.str.contains(season)
                    & result_df.index.str.contains("Reg")
                ][0]
                * 100
            )

        if s != "Seg":
            df_kpi_season.loc[i, "SOS2"] = (
                result_df["deviation"][
                    result_df.index.str.contains(season)
                    & result_df.index.str.contains("SOS2")
                    & result_df.index.str.contains(s)
                ][0]
                * 100
            )

        if s != "2Seg" and s != "Seg":
            df_kpi_season.loc[i, "BigM"] = (
                result_df["deviation"][
                    result_df.index.str.contains(season)
                    & result_df.index.str.contains("Big_M")
                    & result_df.index.str.contains(s)
                ][0]
                * 100
            )

    # change order to align with optimisation result plots
    desired_order = ["BigM", "SOS2", "linear reg"]
    df_kpi_season = df_kpi_season.reindex(columns=desired_order)

    df_kpi_season = df_kpi_season.replace(0, 0.008)

    return df_kpi_season


# plotting


def plot_kpi(kpi):
    kpi_ger = map_kpi_name_ger_en(kpi)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), sharey=True, sharex=True)

    res_def_sommer = create_result_df(kpi_ger, "Sommer")
    res_def_sommer.plot.barh(ax=ax1)

    ax1.set_title("summer")

    res_def_winter = create_result_df(kpi_ger, "Winter")
    res_def_winter.plot.barh(ax=ax2)
    ax2.set_title("winter")

    for ax in [ax1, ax2]:
        ax.set_xlabel("deviation from simulation in %")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        # Add only vertical grid lines to each subplot
        ax.grid(axis="x", linestyle="--")

    # Add a common title to the entire figure
    fig.suptitle(kpi, fontsize=16)

    plt.tight_layout()
    plt.show()


# plot_kpi("Average charging efficiency")
