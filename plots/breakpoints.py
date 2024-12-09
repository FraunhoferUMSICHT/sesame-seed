import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sys

# uncomment to use function in __main__()
# linearization_path = os.path.realpath(
#     os.path.join(os.getcwd(), "src", "storage_models")
# )
# sys.path.append(linearization_path)
# from linearization import find_breakpoints, process_breakpoints

plotstyle_path = os.path.realpath(os.path.join(os.getcwd(), "plots"))
sys.path.append(plotstyle_path)

from plotstyles import Plotstyles

style_inst = Plotstyles()
style_inst.set_pub()


def plot_breakpoints_as_subplots(
    x_data, y_data, number_of_subplots, df_breakpoints, bp_labels, x_label, y_label
):
    if number_of_subplots != len(bp_labels):
        raise ValueError(
            "The number of subplots must be equal to the number breakpoint labels."
        )

    # Calculate the number of rows and columns for the grid
    if number_of_subplots == 3:
        num_cols = 2
        num_rows = 2
    else:
        num_cols = int(np.sqrt(number_of_subplots))
        num_rows = int(np.ceil(number_of_subplots / num_cols))

    # Flatten the axes array if it's 2D to simplify the indexing
    if number_of_subplots == 1:
        fig, axes = plt.subplots(1, 1, figsize=(6, 4), sharex=True)
    else:
        fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 10))

    for i in range(number_of_subplots):
        # collect the right breakpoint data for each axis
        col_label = bp_labels[i]
        col_position = df_breakpoints.columns.get_loc(col_label)
        breakpoints = df_breakpoints.iloc[:, [col_position, col_position + 1]]
        y_col_label = breakpoints.columns[1]

        if number_of_subplots == 1:
            ax = axes
        else:
            ax = axes[i // num_cols, i % num_cols]
            ax.scatter(x_data, y_data, s=10)
            ax.plot(
                breakpoints[col_label],
                breakpoints[y_col_label],
                marker="o",
                linestyle="-",
                color="#B2D235",
            )
            ax.set_title(col_label[1:].replace("_", " "))
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.grid(True)

    # Hide any unused subplots
    if number_of_subplots < num_rows * num_cols:
        for i in range(number_of_subplots, num_rows * num_cols):
            ax = axes[i // num_cols, i % num_cols]
            ax.axis("off")

    plt.tight_layout()
    plt.show()


def plot_breakpoints_processed(
    x_data,
    y_data,
    x_breakpoints,
    y_breakpoints,
    x_bp_processed,
    y_bp_processed,
    x_label,
    y_label,
):
    # create subplots to plot in
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))

    # plot original data
    ax1.scatter(x_data, y_data, s=10)
    ax2.scatter(x_data, y_data, s=10)

    # plot processed breakpoints
    ax1.plot(
        x_bp_processed[1:],
        y_bp_processed[1:],
        marker="o",
        linestyle="-",
        color="#337C99",
    )
    ax2.plot(x_bp_processed, y_bp_processed, marker="o", linestyle="-", color="#337C99")

    # plot original breakpoints
    ax1.plot(x_breakpoints, y_breakpoints, marker="o", linestyle=":", color="#B2D235")

    # format plots
    ax1.grid(True)
    ax2.grid(True)

    fig.suptitle(
        "Piecewise linearization with {0} breakpoints, with (blue) and without (green)"
        " minimal part load".format(len(x_breakpoints.dropna()))
    )

    for ax in [ax1, ax2]:
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

    plt.tight_layout()

    plt.show()


def plot_breakpoints(x_data, y_data, x_breakpoints, y_breakpoints, x_label, y_label):
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))

    # plot original data
    ax.scatter(x_data, y_data, s=10)

    # plot breakpoints
    ax.plot(x_breakpoints, y_breakpoints, marker="o", linestyle="-", color="#B2D235")

    ax.set_title(
        "Piecewise linearization with {0} breakpoints".format(
            len(x_breakpoints.dropna())
        )
    )
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    plt.grid()
    plt.tight_layout()

    plt.show()


def read_data_from_csv(csv_file, x_value_label, y_value_label):
    # read data from cvs file and separate in x and y values
    raw_data = pd.read_csv(csv_file, sep=";")

    x = np.array(raw_data.loc[:, x_value_label])
    y = np.array(raw_data.loc[:, y_value_label])

    return x, y


def __main__():
    # define path to data file
    # choose the data from the design plan
    data_file_name = "caes_storage_losses_data.csv"
    data_file = os.path.realpath(
        os.path.join(os.getcwd(), "design_plan_simulation_results", data_file_name)
    )

    # define column labels of input data
    x_value_label = "SOC_init"
    y_value_label = "soc_loss_spec_hourly"

    x, y = read_data_from_csv(data_file, x_value_label, y_value_label)

    df = pd.read_csv(
        os.path.realpath(os.path.join(os.getcwd(), "test_breakpoints.csv")), sep=";"
    )

    bp_labels = ["x_2_breakpoints", "x_3_breakpoints", "x_2_breakpoints_processed"]

    plot_breakpoints_as_subplots(x, y, 3, df, bp_labels, "$P_{in}$", "$P_{in,stor}$")


# __main__()
