from oemof.solph.components import Transformer

from pyomo.core.base.block import ScalarBlock
from pyomo.environ import Constraint, NonNegativeReals, Var, Set


class Storage(Transformer):
    r"""
    kjhf
    """

    def __init__(
        self,
        el_inputs,
        el_outputs,
        P_MAX_IN,
        P_MAX_OUT,
        SOC_MIN,
        SOC_MAX,
        SOC_INI,
        ETA_IN,
        ETA_OUT,
        ETA_SOC,
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

        # add minimal and maximal state of charge
        self.SOC_MIN = SOC_MIN
        self.SOC_MAX = SOC_MAX

        # add initial state of charge
        self.SOC_INI = SOC_INI

        # add charging and discharging efficiency
        self.ETA_IN = ETA_IN
        self.ETA_OUT = ETA_OUT

        # add storage efficiency
        self.ETA_SOC = ETA_SOC

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

        # defining optimization variables

        # charging power, only allow positive values and zero
        self.P_in = Var(self.STORAGES, m.TIMESTEPS, within=NonNegativeReals)

        # discharging power, only allow positive values and zero
        self.P_out = Var(self.STORAGES, m.TIMESTEPS, within=NonNegativeReals)

        # state of charge, only allow positive values and zero
        self.soc = Var(self.STORAGES, m.TIMESTEPS, within=NonNegativeReals)

        # defining optimization constraints

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

        self.P_out_flow = Constraint(self.STORAGES, m.TIMESTEPS, rule=_P_out_sum_rule)

        # rule for max charging power
        def _P_in_max_rule(block, n, t):
            lhs = block.P_in[n, t]
            rhs = n.P_MAX_IN
            return lhs <= rhs

        self.P_in_max = Constraint(self.STORAGES, m.TIMESTEPS, rule=_P_in_max_rule)

        # rule for max discharging power
        def _P_out_max_rule(block, n, t):
            lhs = block.P_out[n, t]
            rhs = n.P_MAX_OUT
            return lhs <= rhs

        self.P_out_max = Constraint(self.STORAGES, m.TIMESTEPS, rule=_P_out_max_rule)

        # storage balance
        def _SOC_balance_rule(block, n, t):
            if t > 0:
                lhs = block.soc[n, t]
                rhs = (
                    block.soc[n, t - 1] * n.ETA_SOC
                    + n.ETA_IN * block.P_in[n, t] * m.timeincrement[t]
                    - (1 / n.ETA_OUT) * block.P_out[n, t] * m.timeincrement[t]
                )
            else:
                lhs = block.soc[n, t]
                rhs = (
                    n.SOC_INI * n.ETA_SOC
                    + n.ETA_IN * block.P_in[n, t] * m.timeincrement[t]
                    - (1 / n.ETA_OUT) * block.P_out[n, t] * m.timeincrement[t]
                )
            return lhs == rhs

        self.soc_balance = Constraint(
            self.STORAGES, m.TIMESTEPS, rule=_SOC_balance_rule
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

        # # rule for end state of charge
        def _soc_end_rule(block, n):
            lhs = block.soc[n, m.TIMESTEPS.last()]
            rhs = n.SOC_INI
            return lhs >= rhs

        self.soc_end = Constraint(self.STORAGES, rule=_soc_end_rule)
