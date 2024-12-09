from oemof.solph.components import Transformer

from pyomo.core.base.block import ScalarBlock
from pyomo.environ import BuildAction
from pyomo.core import Piecewise
from pyomo.environ import Constraint, Binary, NonNegativeReals, Var, Set

class Storage(Transformer):
    r"""
    ahgö
    """

    def __init__(
        self,
        el_inputs,
        el_outputs,
        P_MAX_IN,
        P_MAX_OUT,
        P_MIN_IN,
        P_MIN_OUT,
        SOC_MIN,
        SOC_MAX,
        SOC_INI,
        p_in_breakpoints,
        p_in_stor_breakpoints,
        p_out_stor_breakpoints,
        p_out_breakpoints,
        *args,
        **kwargs
    ):

        super().__init__(*args, **kwargs)

        # add input and output
        self.el_inputs = el_inputs
        self.el_outputs = el_outputs

        # add maximal charging and discharging power
        self.P_MAX_IN = P_MAX_IN
        self.P_MAX_OUT = P_MAX_OUT

        # add minimal charging an discharging power
        self.P_MIN_IN = P_MIN_IN * P_MAX_IN
        self.P_MIN_OUT = P_MIN_OUT * P_MAX_OUT

        # add minimal and maximal state of charge
        self.SOC_MIN = SOC_MIN
        self.SOC_MAX = SOC_MAX

        # add initial state of charge
        self.SOC_INI = SOC_INI * SOC_MAX

        # add breakpoints for linearization of storage efficiency
        self.p_in_breakpoints = [i * P_MAX_IN for i in p_in_breakpoints]
        self.p_in_stor_breakpoints = [i * P_MAX_IN for i in p_in_stor_breakpoints]
 
        self.p_out_stor_breakpoints = [i * P_MAX_OUT for i in p_out_stor_breakpoints]
        self.p_out_breakpoints = [i * P_MAX_OUT for i in p_out_breakpoints]

        # map specific input flow to standard API using output nodes
        # predecessor (flow from bus)
        input_nodes = list(self.el_inputs.keys())
        input_flows = list(self.el_inputs.values())
        for i in range(len(el_inputs)):
            node = input_nodes[i]
            flow = input_flows[i]
            node.outputs.update({self: flow})

        # map specific output flow to standard API
        self.outputs.update(self.el_outputs)

    def constraint_group(self):
        """
        Returns Block containing constraints for this class
        """
        return StorageBlock


class StorageBlock(ScalarBlock):
    r"""

    Nothing added to the objective function.
    """

    CONSTRAINT_GROUP = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create(self, group=None):
        if group is None:
            return None

        # reference to energy system
        m = self.parent_block()

        # set containing all instances of class Storage
        self.STORAGES = Set(initialize=[n for n in group])

        # set all parameters necessary for implementation of piecwise
        # linear function of efficiency curves using P_in/P_out and
        # P_in_stor/P_out_stor

        # initialize dictionary for breakpoints 
        # stores list (or dict etc.) of breakpoints for each STORAGE
        # breakpoints are the same for each timestep

        self.breakpoints_p_in = {}
        self.func_value_p_in_stor = {}

        self.func_value_p_out = {}
        self.breakpoints_p_out_stor = {}

        def build_breakpoints_p_in(block, n):
            for t in m.TIMESTEPS:
                self.breakpoints_p_in[(n, t)] = n.p_in_breakpoints

        self.p_in_breakpoint_build = BuildAction(
            self.STORAGES, rule=build_breakpoints_p_in
        )

        def build_breakpoints_p_out(block, n):
            for t in m.TIMESTEPS:
                self.breakpoints_p_out_stor[(n, t)] = n.p_out_stor_breakpoints

        self.p_out_breakpoint_build = BuildAction(
            self.STORAGES, rule=build_breakpoints_p_out
        )
      
        def build_breakpoints_p_in_stor(block, n):
            for t in m.TIMESTEPS:
                self.func_value_p_in_stor[(n, t)] = n.p_in_stor_breakpoints

        self.p_in_stor_breakpoint_build = BuildAction(
            self.STORAGES, rule=build_breakpoints_p_in_stor
        )

        def build_breakpoints_p_out_stor(block, n):
            for t in m.TIMESTEPS:
                self.func_value_p_out[(n, t)] = n.p_out_breakpoints

        self.p_out_stor_breakpoint_build = BuildAction(
            self.STORAGES, rule=build_breakpoints_p_out_stor
        )


        # define bounds of P_in, P_in_stor and P_out, P_out_stor

        # bounds are equal to maximum charging/discharging power
        # which is equal to maximum of breakpoints
        # and value at maximum of breakpoints

        lower_bound_p_in = {n: min(n.p_in_breakpoints) for n in group}  
        upper_bound_p_in = {n: max(n.p_in_breakpoints) for n in group}

        lower_bound_p_in_stor = {n: min(n.p_in_stor_breakpoints) for n in group}
        upper_bound_p_in_stor = {n: max(n.p_in_stor_breakpoints) for n in group}

        lower_bound_p_out_stor = {n: min(n.p_out_stor_breakpoints) for n in group}
        upper_bound_p_out_stor = {n: max(n.p_out_stor_breakpoints) for n in group}

        lower_bound_p_out = {n: min(n.p_out_breakpoints) for n in group}
        upper_bound_p_out = {n: max(n.p_out_breakpoints) for n in group}

        def get_p_in_bounds(model, n, t):
            return lower_bound_p_in[n], upper_bound_p_in[n]

        def get_p_in_stor_bounds(model, n, t):
            return lower_bound_p_in_stor[n], upper_bound_p_in_stor[n]

        def get_p_out_bounds(model, n, t):
            return lower_bound_p_out[n], upper_bound_p_out[n]

        def get_p_out_stor_bounds(model, n, t):
            return lower_bound_p_out_stor[n], upper_bound_p_out_stor[n]

        # ---------------------------------------------------------------
        # defining optimization variables
        # ---------------------------------------------------------------

        # charging power, only allow positive values and zero
        self.P_in = Var(self.STORAGES, m.TIMESTEPS, bounds=get_p_in_bounds)

        # actually stored charging power, only allow positive values and zero
        self.P_in_stor = Var(self.STORAGES, m.TIMESTEPS, bounds=get_p_in_stor_bounds)

        # discharging power, only allow positive values and zero
        self.P_out = Var(self.STORAGES, m.TIMESTEPS, bounds=get_p_out_bounds)

        # discharging power that is taken out of the storage volume while
        # discharging with P_out, only allow positive values and zero
        self.P_out_stor = Var(self.STORAGES, m.TIMESTEPS, bounds=get_p_out_stor_bounds)

        # status variable indicating if the storage is charging or not
        self.Y_p_in = Var(self.STORAGES, m.TIMESTEPS, within=Binary)
        # status variable indicating if the storage is discharging or not
        self.Y_p_out = Var(self.STORAGES, m.TIMESTEPS, within=Binary)

        # state of charge, only allow positive values and zero
        self.soc = Var(self.STORAGES, m.TIMESTEPS, within=NonNegativeReals)

        # ---------------------------------------------------------------
        # defining optimization constraints
        # ---------------------------------------------------------------

        # map inflow to charging power
        def _P_in_sum_rule(block, n, t):
            lhs = block.P_in[n, t]
            rhs = sum([m.flow[i, n, t] for i in list(n.el_inputs.keys())])
            return lhs == rhs

        self.P_in_flow = Constraint(self.STORAGES, m.TIMESTEPS, rule=_P_in_sum_rule)

        # map outflow to discharging power
        def _P_out_sum_rule(block, n, t):
            lhs = block.P_out[n, t]
            rhs = sum([m.flow[n, o, t] for o in list(n.el_outputs.keys())])
            return lhs == rhs

        self.P_out_flow = Constraint(
            self.STORAGES, m.TIMESTEPS, rule=_P_out_sum_rule
        )

        # rule for max charging power
        def _P_in_max_rule(block, n, t):
            lhs = block.P_in[n, t]
            rhs = block.Y_p_in[n, t] * n.P_MAX_IN
            return lhs <= rhs

        self.P_in_max = Constraint(self.STORAGES, m.TIMESTEPS, rule=_P_in_max_rule)

        # rule for min charging power
        def _P_in_min_rule(block, n, t):
            lhs = block.P_in[n, t]
            rhs = block.Y_p_in[n, t] * n.P_MIN_IN
            return lhs >= rhs

        self.P_in_min = Constraint(self.STORAGES, m.TIMESTEPS, rule=_P_in_min_rule)

        # rule for max discharging power
        def _P_out_max_rule(block, n, t):
            lhs = block.P_out[n, t]
            rhs = block.Y_p_out[n, t] * n.P_MAX_OUT
            return lhs <= rhs

        self.P_out_max = Constraint(self.STORAGES, m.TIMESTEPS, rule=_P_out_max_rule)

        # rule for min discharging power
        def _P_out_min_rule(block, n, t):
            lhs = block.P_out[n, t]
            rhs = block.Y_p_out[n, t] * n.P_MIN_OUT
            return lhs >= rhs

        self.P_out_min = Constraint(self.STORAGES, m.TIMESTEPS, rule=_P_out_min_rule)

        # rule excluding simultaneously charging and discharging
        def _operation_mode_rule(block, n, t):
            lhs = block.Y_p_in[n, t] + block.Y_p_out[n, t]
            rhs = 1
            return lhs <= rhs

        self.operation_mode = Constraint(
            self.STORAGES, m.TIMESTEPS, rule=_operation_mode_rule
        )

        # storage balance
        def _SOC_balance_rule(block, n, t):
            if t > 0:
                lhs = block.soc[n, t]
                rhs = (
                    block.soc[n, t - 1]
                    + block.P_in_stor[n, t] * m.timeincrement[t]
                    - block.P_out_stor[n, t] * m.timeincrement[t]
                )
            else:
                lhs = block.soc[n, t]
                rhs = (
                    n.SOC_INI
                    + block.P_in_stor[n, t] * m.timeincrement[t]
                    - block.P_out_stor[n, t] * m.timeincrement[t]
                )
            return lhs == rhs

        self.soc_balance = Constraint(
            self.STORAGES, m.TIMESTEPS, rule=_SOC_balance_rule
        )

        # rule for relation between P_in and P_in_stor
        self.pwlf_p_in = Piecewise(
            self.STORAGES,
            m.TIMESTEPS,
            self.P_in_stor,
            self.P_in,
            pw_pts=self.breakpoints_p_in,
            pw_constr_type="EQ",
            f_rule=self.func_value_p_in_stor,
            pw_repn="SOS2",
        )

        # rule for relation between P_out and P_out_stor
        self.pwlf_p_out = Piecewise(
            self.STORAGES,
            m.TIMESTEPS,
            self.P_out,
            self.P_out_stor,
            pw_pts=self.breakpoints_p_out_stor,
            pw_constr_type="EQ",
            f_rule=self.func_value_p_out,
            pw_repn="SOS2",
        )

        # rule for max state of charge
        def _soc_max_rule(block, n, t):
            lhs = block.soc[n, t]
            rhs = n.SOC_MAX
            return lhs <= rhs

        self.soc_max = Constraint(self.STORAGES, m.TIMESTEPS, rule=_soc_max_rule)

        # rule for min state of charge
        def _soc_min_rule(block, n, t):
            lhs = block.soc[n, t]
            rhs = n.SOC_MIN
            return lhs >= rhs

        self.soc_min = Constraint(self.STORAGES, m.TIMESTEPS, rule=_soc_min_rule)

        # rule for end state of charge (same as initial state of charge)
        def _soc_end_rule(block, n):
            lhs = block.soc[n, m.TIMESTEPS.last()]
            rhs = n.SOC_INI
            return lhs >= rhs

        self.soc_end = Constraint(self.STORAGES, rule=_soc_end_rule)

