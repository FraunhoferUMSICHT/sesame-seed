import os
import pandas as pd
import matplotlib.pyplot as plt

import sys

plotstyle_path = os.path.realpath(os.path.join(os.getcwd(), "plots"))
sys.path.append(plotstyle_path)

from plotstyles import Plotstyles

style_inst = Plotstyles()
style_inst.set_pub()


def plot_specific_storage_losses(
    data_file_path,
    constant_efficiency,
    constant_losses,
    linear_losses_slope,
    linear_losses_intercept,
):
    # read original data from simulation of the design plan
    data = pd.read_csv(data_file_path, sep=";")

    # calculate efficiency and storage losses for a constant efficiency
    data["fixed eta_soc"] = constant_efficiency
    data["soc_loss with fixed eta_soc"] = data["SOC_init"] * (1 - data["fixed eta_soc"])

    # calculate efficiency and storage losses for a constant losses
    data["soc_loss fixed"] = constant_losses
    data["eta_soc with fixed soc_loss"] = (
        data["SOC_init"] - data["soc_loss fixed"]
    ) / data["SOC_init"]

    # calculate efficiency and storage losses for a linear losses
    data["soc_loss linear"] = (
        linear_losses_slope * data["SOC_init"] + linear_losses_intercept
    )
    data["eta_soc with linear soc_loss"] = (
        data["SOC_init"] - data["soc_loss linear"]
    ) / data["SOC_init"]

    # plot efficiency and storage losses
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # plot storage losses
    s11 = ax1.scatter(data["SOC_init"], data["soc_loss"], s=10)
    s13 = ax1.scatter(data["SOC_init"], data["soc_loss fixed"], s=8)
    s14 = ax1.scatter(data["SOC_init"], data["soc_loss linear"], s=8)
    s12 = ax1.scatter(data["SOC_init"], data["soc_loss with fixed eta_soc"], s=8)
    ax1.set_title("Storage losses")
    ax1.set_xlabel("soc_ini")

    # plot specific storage losses
    s21 = ax2.scatter(data["SOC_init"], data["soc_loss_spec"] * 3600, s=10)
    s23 = ax2.scatter(data["SOC_init"], data["soc_loss fixed"], s=8)
    s24 = ax2.scatter(data["SOC_init"], data["soc_loss linear"], s=8)
    s22 = ax2.scatter(data["SOC_init"], data["soc_loss with fixed eta_soc"], s=8)
    ax2.set_title("Storage losses per hour")
    ax2.set_xlabel("soc_ini")
    ax2.set_ylim(0, 0.000025)
    # Change the y-axis to floating point format
    ax2.ticklabel_format(style="plain", axis="y")

    # Create a common legend outside the subplots
    fig.legend(
        handles=[s11, s12, s13, s14],
        labels=[
            "original data".format(constant_efficiency),
            "constant efficiency: {0:f}".format(constant_efficiency),
            "constant losses: {0:f}".format(constant_losses),
            "linear losses: slope {0:f}, intercept {1:f}".format(
                linear_losses_slope, linear_losses_intercept
            ),
        ],
        loc="lower center",
        ncol=2,
    )

    # Adjust spacing for the subplots and legend
    plt.subplots_adjust(bottom=0.26, hspace=0.5)

    # Adjust the spacing between subplots
    plt.subplots_adjust(wspace=0.3)

    plt.show()


def plot_storage_losses(
    data_file_path,
    constant_efficiency,
    constant_losses,
    linear_losses_slope,
    linear_losses_intercept,
):
    # read original data from simulation of the design plan
    data = pd.read_csv(data_file_path, sep=";")

    # calculate efficiency and storage losses for a constant efficiency
    data["fixed eta_soc"] = constant_efficiency
    data["soc_loss with fixed eta_soc"] = data["SOC_init"] * (1 - data["fixed eta_soc"])

    # calculate efficiency and storage losses for a constant losses
    data["soc_loss fixed"] = constant_losses
    data["eta_soc with fixed soc_loss"] = (
        data["SOC_init"] - data["soc_loss fixed"]
    ) / data["SOC_init"]

    # calculate efficiency and storage losses for a linear losses
    data["soc_loss linear"] = (
        linear_losses_slope * data["SOC_init"] + linear_losses_intercept
    )
    data["eta_soc with linear soc_loss"] = (
        data["SOC_init"] - data["soc_loss linear"]
    ) / data["SOC_init"]

    # plot efficiency and storage losses
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # plot efficiencies
    s11 = ax1.scatter(data["SOC_init"], data["eta_sp"], s=10)
    s13 = ax1.scatter(data["SOC_init"], data["eta_soc with fixed soc_loss"], s=8)
    s14 = ax1.scatter(data["SOC_init"], data["eta_soc with linear soc_loss"], s=8)
    s12 = ax1.scatter(data["SOC_init"], data["fixed eta_soc"], s=8)
    ax1.set_title("Storage efficiency")
    ax1.set_xlabel("soc_ini")
    ax1.set_ylim(0.85, 1)

    # plot storage losses
    s21 = ax2.scatter(data["SOC_init"], data["soc_loss"], s=10)
    s23 = ax2.scatter(data["SOC_init"], data["soc_loss fixed"], s=8)
    s24 = ax2.scatter(data["SOC_init"], data["soc_loss linear"], s=8)
    s22 = ax2.scatter(data["SOC_init"], data["soc_loss with fixed eta_soc"], s=8)
    ax2.set_title("Storage losses")
    ax2.set_xlabel("soc_ini")

    # Create a common legend outside the subplots
    fig.legend(
        handles=[s11, s12, s13, s14],
        labels=[
            "original data".format(constant_efficiency),
            "constant efficiency: {0:f}".format(constant_efficiency),
            "constant losses: {0:f}".format(constant_losses),
            "linear losses: slope {0:f}, intercept {1:f}".format(
                linear_losses_slope, linear_losses_intercept
            ),
        ],
        loc="lower center",
        ncol=2,
    )

    # Adjust spacing for the subplots and legend
    plt.subplots_adjust(bottom=0.26, hspace=0.5)

    # Adjust the spacing between subplots
    plt.subplots_adjust(wspace=0.3)

    plt.show()


def plot_specific_storage_losses_sorted(
    data_file_path,
):
    # read original data from simulation of the design plan
    data = pd.read_csv(data_file_path, sep=";")
    sub_hour_data = data[data["t_sp"] < 3600]
    sub_12hour_data = data[(data["t_sp"] >= 3600) & (data["t_sp"] < 12 * 3600)]
    sub_24hour_data = data[(data["t_sp"] >= 12 * 3600) & (data["t_sp"] < 24 * 3600)]
    sub_2days_data = data[(data["t_sp"] >= 24 * 3600) & (data["t_sp"] < 2 * 24 * 3600)]
    sub_3days_data = data[
        (data["t_sp"] >= 2 * 24 * 3600) & (data["t_sp"] < 3 * 24 * 3600)
    ]

    # plot efficiency and storage losses
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))

    # plot efficiencies
    s11 = ax1.scatter(data["SOC_init"], data["eta_sp"], s=10)
    s12 = ax1.scatter(sub_3days_data["SOC_init"], sub_3days_data["eta_sp"], s=10)
    s13 = ax1.scatter(sub_2days_data["SOC_init"], sub_2days_data["eta_sp"], s=10)
    s14 = ax1.scatter(sub_24hour_data["SOC_init"], sub_24hour_data["eta_sp"], s=10)
    s15 = ax1.scatter(sub_12hour_data["SOC_init"], sub_12hour_data["eta_sp"], s=10)
    s16 = ax1.scatter(sub_hour_data["SOC_init"], sub_hour_data["eta_sp"], s=10)
    ax1.set_title("Storage efficiency")
    ax1.set_xlabel("soc_ini")

    # plot storage losses
    s21 = ax2.scatter(data["SOC_init"], data["soc_loss"], s=10)
    s22 = ax2.scatter(sub_3days_data["SOC_init"], sub_3days_data["soc_loss"], s=10)
    s23 = ax2.scatter(sub_2days_data["SOC_init"], sub_2days_data["soc_loss"], s=10)
    s24 = ax2.scatter(sub_24hour_data["SOC_init"], sub_24hour_data["soc_loss"], s=10)
    s25 = ax2.scatter(sub_12hour_data["SOC_init"], sub_12hour_data["soc_loss"], s=10)
    s26 = ax2.scatter(sub_hour_data["SOC_init"], sub_hour_data["soc_loss"], s=10)
    ax2.set_title("Storage losses")
    ax2.set_xlabel("soc_ini")

    # plot specific storage losses
    s31 = ax3.scatter(data["SOC_init"], data["soc_loss_spec"] * 3600, s=10)
    s32 = ax3.scatter(
        sub_3days_data["SOC_init"], sub_3days_data["soc_loss_spec"] * 3600, s=10
    )
    s33 = ax3.scatter(
        sub_2days_data["SOC_init"], sub_2days_data["soc_loss_spec"] * 3600, s=10
    )
    s34 = ax3.scatter(
        sub_24hour_data["SOC_init"], sub_24hour_data["soc_loss_spec"] * 3600, s=10
    )
    s35 = ax3.scatter(
        sub_12hour_data["SOC_init"], sub_12hour_data["soc_loss_spec"] * 3600, s=10
    )
    s36 = ax3.scatter(
        sub_hour_data["SOC_init"], sub_hour_data["soc_loss_spec"] * 3600, s=10
    )
    ax3.set_title("Storage losses per hour")
    ax3.set_xlabel("soc_ini")
    # Change the y-axis to floating point format
    ax3.ticklabel_format(style="plain", axis="y")

    # plot storage losses over time
    s41 = ax4.scatter(data["t_sp"], data["soc_loss"], s=10)
    s42 = ax4.scatter(sub_3days_data["t_sp"], sub_3days_data["soc_loss"], s=10)
    s43 = ax4.scatter(sub_2days_data["t_sp"], sub_2days_data["soc_loss"], s=10)
    s44 = ax4.scatter(sub_24hour_data["t_sp"], sub_24hour_data["soc_loss"], s=10)
    s45 = ax4.scatter(sub_12hour_data["t_sp"], sub_12hour_data["soc_loss"], s=10)
    s246 = ax4.scatter(sub_hour_data["t_sp"], sub_hour_data["soc_loss"], s=10)
    ax4.set_title("Storage losses")
    ax4.set_xlabel("t_sp")

    # Create a common legend outside the subplots
    fig.legend(
        handles=[s11, s12, s13, s14, s15, s16],
        labels=[
            "original data",
            "t_sp < 3 days",
            "t_sp < 2 days",
            "t_sp < 1 day",
            "t_sp < 12 hours",
            "t_sp < 1 hour",
        ],
        loc="lower center",
        ncol=3,
    )

    # Adjust spacing for the subplots and legend
    plt.subplots_adjust(bottom=0.17, hspace=0.5)

    # Adjust the spacing between subplots
    plt.subplots_adjust(wspace=0.25)

    plt.show()


def __main__():
    constant_efficiency = 0.999
    constant_losses = 0.000023
    linear_losses_slope = -0.00001
    linear_losses_intercept = 0.00002

    data_file_path = os.path.realpath(
        os.path.join(
            os.getcwd(),
            "design_plan_simulation_results",
            "caes_storage_losses_data.csv",
        )
    )

    plot_specific_storage_losses_sorted(
        data_file_path,
        constant_efficiency,
        constant_losses,
        linear_losses_slope,
        linear_losses_intercept,
    )


# __main__()
