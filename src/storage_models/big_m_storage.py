from oemof.solph.components import Transformer

from pyomo.core.base.block import ScalarBlock
from pyomo.environ import BuildAction
from pyomo.environ import Constraint, Binary, NonNegativeReals, Var, Set


# ---------------------------------------------------------------------
# Helper functions - Calculation of slope and intercept
# ---------------------------------------------------------------------
def slope(x1, y1, x2, y2):
    a = (y2 - y1) / (x2 - x1)
    return a

def intercept(x1, y1, a):
    b = y1 - a * x1
    return b

class Storage(Transformer):
    r"""
    öaSHÖh
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

        # ---------------------------------------------------------------------
        # calculation of parameters a (slope) and b (intercept) for each segment
        # of the piecewise linearization of the storage efficiency
        # ---------------------------------------------------------------------

        if len(self.p_in_breakpoints) != len(self.p_out_breakpoints):
            raise ValueError(
                "The number of segments for charging and discharging have to be equal!"
            )

        # number of breakpoints
        K = [i for i in range(len(self.p_in_breakpoints))]
        # number of segments
        S = [i for i in range(len(self.p_in_breakpoints) - 1)]

        # ---------------------------------------------------------------------
        # slope and intercept for each segment - Charging
        # ---------------------------------------------------------------------

        # dictionary containing the slope for each segment S
        self.AS = {}
        for s in range(len(S)):
            a = slope(
                self.p_in_breakpoints[s],
                self.p_in_stor_breakpoints[s],
                self.p_in_breakpoints[s + 1],
                self.p_in_stor_breakpoints[s + 1],
            )
            self.AS[s] = a

        # dictionary containing the intercept for each segment S
        self.BS = {}
        for s in range(len(S)):
            b = intercept(
                self.p_in_breakpoints[s], self.p_in_stor_breakpoints[s], self.AS[s]
            )
            self.BS[s] = b
         
        # ---------------------------------------------------------------------
        # slope and intercept for each segment - Discharging
        # ---------------------------------------------------------------------

        # dictionary containing the slope for each segment S
        self.AS_out = {}
        for s in range(len(S)):
            a = slope(
                self.p_out_stor_breakpoints[s],
                self.p_out_breakpoints[s],
                self.p_out_stor_breakpoints[s + 1],
                self.p_out_breakpoints[s + 1],
            )
            self.AS_out[s] = a

        # dictionary containing the intercept for each segment S
        self.BS_out = {}
        for s in range(len(S)):
            b = intercept(
                self.p_out_stor_breakpoints[s], self.p_out_breakpoints[s], self.AS_out[s]
            )
            self.BS_out[s] = b

        # ----------------------------------------------------------------------
        # calculation of Big M values - Charging
        # ----------------------------------------------------------------------

        # number of Big M values (=necessary equations)
        MC = [i for i in range(4)]

        # for each segment four Big M values are needed for
        # the four equations:
        # 0: y>=, 1: y<=, 2: x>=, 3: x<=

        # dictionary containing the Big M values for each segment S
        self.BIG_M = {}

        for s in S:
            # equation 0: y >=
            bm = []
            for k in K:
                bm.append(
                    self.p_in_stor_breakpoints[k]
                    - self.AS[s] * self.p_in_breakpoints[k]
                    - self.BS[s]
                )
            self.BIG_M[MC[0], s] = -min(bm)

            # equation 1: y <=
            bm = []
            for k in K:
                bm.append(
                    self.p_in_stor_breakpoints[k]
                    - self.AS[s] * self.p_in_breakpoints[k]
                    - self.BS[s]
                )
            self.BIG_M[MC[1], s] = max(bm)

            # equation 2: x >=
            bm = []
            bm.append(self.p_in_breakpoints[s] - min(self.p_in_breakpoints))
            bm.append(0)
            self.BIG_M[MC[2], s] = max(bm)

            # equation 3: x <=
            bm = []
            bm.append(max(self.p_in_breakpoints) - self.p_in_breakpoints[s + 1])
            bm.append(0)
            self.BIG_M[MC[3], s] = max(bm)


        # ---------------------------------------------------------------------
        # calculation of Big M values - Discharging
        # ---------------------------------------------------------------------

        # dictionary containing the Big M values for each segment S
        self.BIG_M_out = {}

        for s in S:
            # equation 0: y >=
            bm = []
            for k in K:
                bm.append(
                    self.p_out_breakpoints[k]
                    - self.AS_out[s] * self.p_out_stor_breakpoints[k]
                    - self.BS_out[s]
                )
            self.BIG_M_out[MC[0], s] = -min(bm)

            # equation 1: y <=
            bm = []
            for k in K:
                bm.append(
                    self.p_out_breakpoints[k]
                    - self.AS_out[s] * self.p_out_stor_breakpoints[k]
                    - self.BS_out[s]
                )
            self.BIG_M_out[MC[1], s] = max(bm)

            # equation 2: x >=
            bm = []
            bm.append(self.p_out_stor_breakpoints[s] - min(self.p_out_stor_breakpoints))
            bm.append(0)
            self.BIG_M_out[MC[2], s] = max(bm)

            # equation 3: x <=
            bm = []
            bm.append(
                max(self.p_out_stor_breakpoints) - self.p_out_stor_breakpoints[s + 1]
            )
            bm.append(0)
            self.BIG_M_out[MC[3], s] = max(bm)


        # ---------------------------------------------------------------------

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

        # set containing all instances of class LinearStorage
        self.STORAGES = Set(initialize=[n for n in group])

        # set all parameters necessary for implementation of piecwise
        # linear function of efficiency curves using P_in/P_out and
        # P_in_stor/P_out_stor

        # initialize dictionary for slope and intercept of each segment
  
        self.as_in = {}

        def build_as_in(block, n):
            for s in range(len(n.AS)):
                self.as_in[(n, s)] = n.AS[s]

        self.as_in_build = BuildAction(self.STORAGES, rule=build_as_in)

        self.bs_in = {}

        def build_bs_in(block, n):
            for s in range(len(n.BS)):
                self.bs_in[(n, s)] = n.BS[s]

        self.bs_in_build = BuildAction(self.STORAGES, rule=build_bs_in)

        self.as_out = {}

        def build_as_out(block, n):
            for s in range(len(n.AS_out)):
                self.as_out[(n, s)] = n.AS_out[s]

        self.as_out_build = BuildAction(self.STORAGES, rule=build_as_out)

        self.bs_out = {}

        def build_bs_out(block, n):
            for s in range(len(n.BS_out)):
                self.bs_out[(n, s)] = n.BS_out[s]

        self.bs_out_build = BuildAction(self.STORAGES, rule=build_bs_out)

        # initialize dictionary for Big M values of each segment

        self.big_m_in = {}

        def build_big_m_in(block, n):
            for key, value in n.BIG_M.items():
                self.big_m_in[(n, key)] = value

        self.big_m_in_build = BuildAction(self.STORAGES, rule=build_big_m_in)

        self.big_m_out = {}

        def build_big_m_out(block, n):
            for key, value in n.BIG_M_out.items():
                self.big_m_out[(n, key)] = value

        self.big_m_out_build = BuildAction(self.STORAGES, rule=build_big_m_out)

        self.x_in_data = {}

        # initialize dictionary for x-breakpoints of each segment

        def build_x_in_data(block, n):
            for k in range(len(n.BS) + 1):
                self.x_in_data[n, k] = n.p_in_breakpoints[k]

        self.build_x_in_data = BuildAction(self.STORAGES, rule=build_x_in_data)

        self.x_out_data = {}

        def build_x_out_data(block, n):
            for k in range(len(n.BS_out) + 1):
                self.x_out_data[n, k] = n.p_out_stor_breakpoints[k]

        self.build_x_out_data = BuildAction(self.STORAGES, rule=build_x_out_data)

        # ---------------------------------------------------------------
        # defining optimization variables
        # ---------------------------------------------------------------

        # charging power, only allow positive values and zero
        self.P_in = Var(self.STORAGES, m.TIMESTEPS, within=NonNegativeReals)

        # actually stored charging power, only allow positive values and zero
        self.P_in_stor = Var(self.STORAGES, m.TIMESTEPS, within=NonNegativeReals)

        # discharging power, only allow positive values and zero
        self.P_out = Var(self.STORAGES, m.TIMESTEPS, within=NonNegativeReals)

        # discharging power that is taken out of the storage volume while
        # discharging with P_out, only allow positive values and zero
        self.P_out_stor = Var(
            self.STORAGES, m.TIMESTEPS, within=NonNegativeReals
        )

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

        # ---------------------------------------------------------------
        # rule for relation between P_in and P_in_stor
        # for each segment four equations are needed:
        # 0: y>=, 1: y<=, 2: x>=, 3: x<=
        # ---------------------------------------------------------------

        # initialize pyomo set with number of segments
        S = [i for i in range(len(self.as_in) - 1)]
        self.s = Set(initialize=S)

        # initialize binary variable for each segment
        self.delta = Var(self.STORAGES, self.s, m.TIMESTEPS, within=Binary)

        # equation 0: y >=
        def rule_0(block, n, s, t):
            lhs = self.P_in_stor[n, t]
            rhs = (
                self.as_in[n, s] * self.P_in[n, t]
                + self.bs_in[n, s]
                - self.big_m_in[n, (0, s)] * (1 - self.delta[n, s, t])
            )
            return lhs >= rhs

        self.constr_0 = Constraint(self.STORAGES, self.s, m.TIMESTEPS, rule=rule_0)

        # equation 1: y <=
        def rule_1(block, n, s, t):
            lhs = self.P_in_stor[n, t]
            rhs = (
                self.as_in[n, s] * self.P_in[n, t]
                + self.bs_in[n, s]
                + self.big_m_in[n, (1, s)] * (1 - self.delta[n, s, t])
            )
            return lhs <= rhs

        self.constr_1 = Constraint(self.STORAGES, self.s, m.TIMESTEPS, rule=rule_1)

        # equation 2: x >=
        def rule_2(block, n, s, t):
            lhs = self.P_in[n, t]
            rhs = self.x_in_data[n, s] - self.big_m_in[n, (2, s)] * (
                1 - self.delta[n, s, t]
            )
            return lhs >= rhs

        self.constr_2 = Constraint(self.STORAGES, self.s, m.TIMESTEPS, rule=rule_2)

        # equation 3: x <=
        def rule_3(block, n, s, t):
            lhs = self.P_in[n, t]
            rhs = self.x_in_data[n, s + 1] + self.big_m_in[n, (3, s)] * (
                1 - self.delta[n, s, t]
            )
            return lhs <= rhs

        self.constr_3 = Constraint(self.STORAGES, self.s, m.TIMESTEPS, rule=rule_3)

        # equation for binary variables: only ever one binary variable can be different from zero
        def bin_sum_rule(block, n, t):
            lhs = sum(self.delta[n, s, t] for s in self.s)
            rhs = 1
            return lhs == rhs

        self.constr_delta = Constraint(self.STORAGES, m.TIMESTEPS, rule=bin_sum_rule)

        
        # ---------------------------------------------------------------
        # rule for relation between P-out and P_out_stor
        # for each segment four equations are needed:
        # 0: y>=, 1: y<=, 2: x>=, 3: x<=
        # ---------------------------------------------------------------

        # initialize binary variable for each segment
        self.delta_out = Var(self.STORAGES, self.s, m.TIMESTEPS, within=Binary)

        # equation 0: y >=
        def rule_0_out(block, n, s, t):
            lhs = self.P_out[n, t]
            rhs = (
                self.as_out[n, s] * self.P_out_stor[n, t]
                + self.bs_out[n, s]
                - self.big_m_out[n, (0, s)] * (1 - self.delta_out[n, s, t])
            )
            return lhs >= rhs

        self.constr_0_out = Constraint(
            self.STORAGES, self.s, m.TIMESTEPS, rule=rule_0_out
        )

        # equation 1: y <=
        def rule_1_out(block, n, s, t):
            lhs = self.P_out[n, t]
            rhs = (
                self.as_out[n, s] * self.P_out_stor[n, t]
                + self.bs_out[n, s]
                + self.big_m_out[n, (1, s)] * (1 - self.delta_out[n, s, t])
            )
            return lhs <= rhs

        self.constr_1_out = Constraint(
            self.STORAGES, self.s, m.TIMESTEPS, rule=rule_1_out
        )

        # equation 2: x >=
        def rule_2_out(block, n, s, t):
            lhs = self.P_out_stor[n, t]
            rhs = self.x_out_data[n, s] - self.big_m_out[n, (2, s)] * (
                1 - self.delta_out[n, s, t]
            )
            return lhs >= rhs

        self.constr_2_out = Constraint(
            self.STORAGES, self.s, m.TIMESTEPS, rule=rule_2_out
        )

        # equation 3: x <=
        def rule_3_out(block, n, s, t):
            lhs = self.P_out_stor[n, t]
            rhs = self.x_out_data[n, s + 1] + self.big_m_out[n, (3, s)] * (
                1 - self.delta_out[n, s, t]
            )
            return lhs <= rhs

        self.constr_3_out = Constraint(
            self.STORAGES, self.s, m.TIMESTEPS, rule=rule_3_out
        )

        # equation for binary variables: only ever one binary variable can be different from zero
        def bin_sum_rule_out(block, n, t):
            lhs = sum(self.delta_out[n, s, t] for s in self.s)
            rhs = 1
            return lhs == rhs

        self.constr_delta_out = Constraint(
            self.STORAGES, m.TIMESTEPS, rule=bin_sum_rule_out
        )

        # -----------------------------------------------------------------------------

        # rule for maxi state of charge
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

        # # rule for end state of charge
        def _soc_end_rule(block, n):
            lhs = block.soc[n, m.TIMESTEPS.last()]
            rhs = n.SOC_INI
            return lhs >= rhs

        self.soc_end = Constraint(self.STORAGES, rule=_soc_end_rule)
