import os
import numpy as np
import pandas as pd
import pwlf
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


def find_constant_efficiency(
    csv_file, x_value_label, y_value_label, eff_value_label=None
):
    """
    Function finds three different constant efficiencies, for a given data set x and y,
    for which the efficiency is defined by y divided by x.

    Parameters
    ----------
    csv_file : String
        path to csv-file containing x and y data for which the efficiency is to be
        calculated, ";" should be used as separator
    x_value_label : String
        name of the column containing the x values of the data for which the efficiency
        is to be calculated.
    y_value_label : String
        name of the column containing the y values of the data for which the efficiency
        is to be calculated.
        eff_value_label : String, optional
        if existing,  name of the column containing the efficiency values of the data
        for which the efficiency is to be calculated.

    Returns
    -------
    efficiency_reg : scalar
        constant efficiency corresponding to the slope of a linear regression model
    efficiency_max : scalar
        constant efficiency corresponding to the maximum efficiency given
    efficiency_mean : scalar
        constant efficiency corresponding to the mean efficiency given

    """

    # read data from cvs file and separate in x and y values
    raw_data = pd.read_csv(csv_file, sep=";")

    x = np.array(raw_data.loc[:, x_value_label])
    y = np.array(raw_data.loc[:, y_value_label])

    # Perform linear regression, without a intercept
    regression_model = LinearRegression(fit_intercept=False)
    regression_model.fit(x.reshape(-1, 1), y)

    # Get the slope of the fitted line
    efficiency_reg = regression_model.coef_[0]

    # calculate maximum efficiency
    if eff_value_label == None:
        eta = y / x
    else:
        eta = np.array(raw_data.loc[:, eff_value_label])

    efficiency_max = max(eta)

    # calculate mean efficiency
    efficiency_mean = np.mean(eta)

    return efficiency_reg, efficiency_max, efficiency_mean


def find_breakpoints(csv_file, x_value_label, y_value_label, number_of_breakpoints):
    """
    Function finds optimal breakpoints for given x and y data and number of breakpoints.
    The function uses the pwlf package to do so. The documentation for pwlf can be found at
    https://jekel.me/piecewise_linear_fit_py/pwlf.html.
    pwlf needs the number of segments as an input, therefore, the lower bound for
    number_of_breakpoints is 2.

    Parameters
    ----------
    csv_file : String
        path to csv-file containing x and y data for which the breakpoints are to be
        calculated, ";" should be used as separator
    x_value_label : String
        name of the column containing the x values of the data for which the breakpoints
        are to be calculated.
    y_value_label : String
        name of the column containing the y values of the data for which the breakpoints
        are to be calculated.
    number_of_breakpoints : int,
        number of breakpoints to be calculated

    Returns
    -------
    x_breakpoints : np.array of length L
        x values of all breakpoints
    y_breakpoints : np.array of length L
        y values of all breakpoints

    """

    # read data from cvs file and separate in x and y values
    raw_data = pd.read_csv(csv_file, sep=";")

    x = np.array(raw_data.loc[:, x_value_label])
    y = np.array(raw_data.loc[:, y_value_label])

    # Normalize x
    lbd_x, ubd_x = np.min(x), np.max(x)
    x_norm = (x - lbd_x) / (ubd_x - lbd_x)

    # Obtain breakpoints
    model_x = pwlf.PiecewiseLinFit(x_norm, y)
    x_breakpoints = model_x.fit(number_of_breakpoints - 1)
    y_breakpoints = model_x.predict(x_breakpoints)

    # Rescale x
    x_breakpoints = x_breakpoints * (ubd_x - lbd_x) + lbd_x

    return x_breakpoints, np.array(y_breakpoints)


def process_breakpoints(x_breakpoints, y_breakpoints, x_min, x_max):
    """
    Process a given set of breakpoints to explicitly contain the points (0,0),
    (x_min, y_mpl) and (x_max, y_max).
    These points are necessary to correctly implement a piecewise implementation in
    a MILP model.
    Since 0, x_min and x_max might not be contained within in the original data set used
    to calculate the breakpoints, these have to be added manually.

    Parameters
    ----------
    x_breakpoints : np.array of length n
        x values of the input breakpoints
    y_breakpoints : np.array of length n
        y values of the input breakpoints
    x_min : scalar
        minimal value of x, different from 0
    x_max : scalar
        maximal value of x

    Returns
    -------
    x_bp_processed : np.array of length n+1
        x values of processed breakpoints incl. 0, x_min and x_max
    y_bp_processed : np.array of length n+1
        y values of processed breakpoints incl. 0, y_mpl and y_max

    """

    # get x and y breakpoints of the first segment
    x_bp = [x_breakpoints[0], x_breakpoints[1]]
    y_bp = [y_breakpoints[0], y_breakpoints[1]]

    # calculate slope and intercept of the first segment
    slope, intercept = np.polyfit(x_bp, y_bp, 1)
    # calculate the y value at x_min (minimal part load)
    y_mpl = slope * x_min + intercept

    # efficiency cannot be below zero
    # in this case set breakpoint to zero
    if y_mpl < 0:
        y_mpl = 0

    # get x and y breakpoints of the last segment
    x_bp = [x_breakpoints[-2], x_breakpoints[-1]]
    y_bp = [y_breakpoints[-2], y_breakpoints[-1]]
    # calculate slope and intercept of the last segment
    slope, intercept = np.polyfit(x_bp, y_bp, 1)
    # calculate the y value at x_max
    y_max = slope * x_max + intercept

    # delete the first and last breakpoint of the given data and replace
    # by x_min and x_max
    x_bp_processed = np.concatenate(
        ([x_min], np.delete(x_breakpoints, [0, -1]), [x_max])
    )
    if x_min != 0:
        # add 0 at the beginning of the breakpoints
        x_bp_processed = np.insert(x_bp_processed, 0, [0])

    # delete the first and last breakpoint of the given data and replace
    # by y_mpl and y_max
    y_bp_processed = np.concatenate(
        ([y_mpl], np.delete(y_breakpoints, [0, -1]), [y_max])
    )
    if x_min != 0:
        # add 0 at the beginning of the breakpoints
        y_bp_processed = np.insert(y_bp_processed, 0, [0])

    return (x_bp_processed, y_bp_processed)


def save_breakpoints_to_csv(
    x_breakpoints,
    y_breakpoints,
    res_decimals,
    res_file_path,
):
    """
    Saves given breakpoints to csv in two formats:
    as table with x_breakpoints and y breakpoints as columns
    as string with x_breakpoints and y breakpoints as individual strings separated by ', '

    Parameters
    ----------
    x_breakpoints : np.array of length n
        x values of the input breakpoints
    y_breakpoints : np.array of length n
        y values of the input breakpoints
    res_file_path : string
        path to folder, where files are to be saved

    Returns
    -------
    -

    """

    # save breakpoints to csv-file for further analysis
    breakpoints = pd.DataFrame(data=[x_breakpoints, y_breakpoints]).transpose()
    breakpoints.columns = ["x_breakpoints", "y_breakpoints"]

    # create export directory if necessary
    if not os.path.exists(res_file_path):
        os.makedirs(res_file_path)

    filename = str(len(x_breakpoints)) + "_breakpoints.csv"
    file = os.path.realpath(os.path.join(res_file_path, filename))
    breakpoints.to_csv(file, sep=";")

    # save breakpoints to csv-file for "scenario_table.csv"
    str_x_breakpoints = ", ".join(
        "{:.{}f}".format(x, res_decimals) for x in x_breakpoints
    )
    str_y_breakpoints = ", ".join(
        "{:.{}f}".format(y, res_decimals) for y in y_breakpoints
    )

    breakpoints = pd.DataFrame(data=[str_x_breakpoints, str_y_breakpoints]).transpose()
    breakpoints.columns = ["x_breakpoints", "y_breakpoints"]

    filename = str(len(x_breakpoints)) + "_breakpoints_as_string.csv"
    file = os.path.realpath(os.path.join(res_file_path, filename))
    breakpoints.to_csv(file, sep=";")


def loop_breakpoint_calculation(
    data_file,
    res_file_path,
    x_value_label,
    y_value_label,
    minimal_number_of_breakpoints,
    maximum_number_of_breakpoints,
    x_min,
    x_max,
    res_decimals,
    log_msg: bool = True,
):
    """
    loops over a range of number of breakpoints, each time calculating, processing and
    saving the calculated breakpoints to csv files

    Parameters
    ----------
    data_file : String
        path to csv-file containing x and y data for which the breakpoints are to be
        calculated, ";" should be used as separator
    res_file_path : string
        path to folder, where files are to be saved
    x_value_label : String
        name of the column containing the x values of the data for which the breakpoints
        are to be calculated.
    y_value_label : String
        name of the column containing the y values of the data for which the breakpoints
        are to be calculated.
    minimal number_of_breakpoints : int,
        lower bound of number of breakpoints to be calculated
    maximum number_of_breakpoints : int,
        upper bound of number of breakpoints to be calculated
    x_min : scalar
        minimal value of x, different from 0
    x_max : scalar
        maximal value of x
    log_msg: bool
        specifies if logging message should be displayed while calculating

    Returns
    -------
    breakpoint_dict : dict
        dictionary containing the calculated x and y breakpoints as well as the
        processed x and y processed. The keys are in the form: x_{n}_breakpoints,
        y_{n}_breakpoints and x_{n}_breakpoints_processed, y_{n}_breakpoints_processed
        respectively

    """

    # log message
    if log_msg:
        print("\nCalculating breakpoints:")
        print("--------------------------")

    # initialize result dict
    res_dict = {}

    for n in range(minimal_number_of_breakpoints, maximum_number_of_breakpoints + 1):
        # log message
        if log_msg:
            print("\nCalculating breakpoints for {0} breakpoints:".format(n))

        # calculate breakpoints
        x_breakpoints, y_breakpoints = find_breakpoints(
            data_file, x_value_label, y_value_label, n
        )
        # log message
        if log_msg:
            print(
                "\nThe breakpoints based on the original data are: \n",
                "\t x breakpoints: ",
                x_breakpoints,
                "\n\t y breakpoints: ",
                y_breakpoints,
            )

        # save breakpoints to results dict
        res_dict["x_" + str(n) + "_breakpoints"] = x_breakpoints
        res_dict["y_" + str(n) + "_breakpoints"] = y_breakpoints

        # process breakpoints to include 0, x_min and x_max
        x_bp_processed, y_bp_processed = process_breakpoints(
            x_breakpoints, y_breakpoints, x_min, x_max
        )
        # log message
        if log_msg:
            print(
                "\nThe breakpoints including 0, x_min and x_max are: \n",
                "\t x breakpoints: ",
                x_bp_processed,
                "\n\t y breakpoints: ",
                y_bp_processed,
            )

        # save processed breakpoints to results dict
        res_dict["x_" + str(n) + "_breakpoints_processed"] = x_bp_processed
        res_dict["y_" + str(n) + "_breakpoints_processed"] = y_bp_processed

        # log message
        if log_msg:
            print("\nsaving results to ", res_file_path)

        # save breakpoints to csv
        save_breakpoints_to_csv(
            x_bp_processed, y_bp_processed, res_decimals, res_file_path
        )

        # log message
        if log_msg:
            print("\nDone calculating breakpoints for {0} breakpoints:".format(n))
            print("-------------------------------------------------")

    # log message
    if log_msg:
        print("\nDone calculating.")
        print("-------------------\n")

    # save breakpoints in dataframe
    df_breakpoints = pd.DataFrame.from_dict(res_dict, orient="index").transpose()

    return df_breakpoints


def __main__():
    # define path to data file
    data_file = os.path.realpath(
        os.path.join(
            os.getcwd(),
            "design_plan_simulation_results",
            "phs_charging_efficiency_data.csv",
        )
    )

    # define path to results file
    res_file_path = os.path.realpath(
        os.path.join(
            os.getcwd(), "src", "data", "breakpoint_calculation_results", "example"
        )
    )

    # define column labels of input data
    x_value_label = "P_in_rel"
    y_value_label = "eta_in"

    # define number of breakpoints to be calculated
    minimal_number_of_breakpoints = 2
    maximum_number_of_breakpoints = 3

    # minimum and maximum x value to bound the breakpoints
    x_min = 0.1
    x_max = 1

    # specify if output to terminal is to be displayed
    log_msg = False

    # calculate breakpoints
    breakpoint_dict = loop_breakpoint_calculation(
        data_file,
        res_file_path,
        x_value_label,
        y_value_label,
        minimal_number_of_breakpoints,
        maximum_number_of_breakpoints,
        x_min,
        x_max,
        log_msg,
    )

    # save breakpoints in dataframe
    df_breakpoints = pd.DataFrame.from_dict(breakpoint_dict, orient="index").transpose()

    print("\n------------------- breakpoints -----------------\n")
    print(df_breakpoints)
    print("\n-------------------------------------------------\n")


# __main__()
