# PopulationSim
# See full license in LICENSE.txt.

import logging
import numpy as np
import pandas as pd

from populationsim.core.config import setting
from .balancers import np_balancer_py, np_balancer_numba
from .constants import (
    DEFAULT_MAX_ITERATIONS,
    MAX_INT,
    MIN_IMPORTANCE,
    MIN_CONTROL_VALUE,
)

logger = logging.getLogger(__name__)


class ListBalancer:
    """
    Single-geography list balancer using Newton-Raphson method with control relaxation.

    Takes a list of households with initial weights assigned to each household, and updates those
    weights in such a way as to match the marginal distribution of control variables while
    minimizing the change to the initial weights. Uses Newton-Raphson method with control
    relaxation.

    The resulting weights are float weights, so need to be integerized to integer household weights
    """

    def __init__(
        self,
        incidence_table,
        initial_weights,
        control_totals,
        control_importance_weights,
        lb_weights,
        ub_weights,
        master_control_index,
        max_iterations,
        use_numba,
        numba_precision,
    ):
        """
        Parameters
        ----------
        incidence_table : pandas DataFrame
            incidence table with only columns for controls to balance
        initial_weights : pandas Series
            initial weights of households in incidence table (in same order)
        control_totals : pandas Series or numpy array
            control totals (in same order as incidence_table columns)
        control_importance_weights : pandas Series
            importance weights of controls (in same order as incidence_table columns)
        lb_weights : pandas Series, numpy array, or scalar
            upper bound on balanced weights for hhs in incidence_table (in same order)
        ub_weights : pandas Series, numpy array, or scalar
            lower bound on balanced weights for hhs in incidence_table (in same order)
        master_control_index
            index of the total_hh_controsl column in controls (and incidence_table columns)
        max_iterations : int
            maximum number of iterations to run balancing algorithm
        use_numba : bool
            whether to use numba for performance optimization
        numba_precision : str
            precision of the Numba calculations, either 'float64' or 'float32'.
        """

        assert isinstance(incidence_table, pd.DataFrame)
        assert len(initial_weights) == len(incidence_table.index)

        self.incidence_table = incidence_table
        self.incidence = incidence_table.values.T
        self.sample_count = len(incidence_table.index)
        self.control_count = len(incidence_table.columns)
        self.control_totals = np.asarray(control_totals)
        self.initial_weights = np.asarray(initial_weights, dtype=np.float64)
        self.control_importance_weights = (
            np.asarray(control_importance_weights)
            if control_importance_weights is not None
            else np.full(self.control_count, MIN_IMPORTANCE)
        )
        self.lb_weights = (
            np.asarray(lb_weights, dtype=np.float64)
            if lb_weights is not None
            else np.zeros(self.sample_count)
        )
        self.ub_weights = (
            np.asarray(ub_weights, dtype=np.float64)
            if ub_weights is not None
            else np.full(self.sample_count, MAX_INT)
        )
        self.max_iterations = max_iterations
        self.use_numba = use_numba
        self.numba_precision = numba_precision
        self.master_control_index = (
            -1 if master_control_index is None else master_control_index
        )

        # Validation
        if not (
            -1 == self.master_control_index
            or 0 <= self.master_control_index < self.control_count
        ):
            raise ValueError(
                f"master_control_index={self.master_control_index} is out of bounds"
            )
        assert self.incidence.shape == (self.control_count, self.sample_count)
        assert self.control_totals.shape[0] == self.control_count
        assert self.control_importance_weights.shape[0] == self.control_count

        # Prepare bounds
        self.weights_lower_bound = (
            np.full(self.sample_count, self.lb_weights)
            if np.isscalar(self.lb_weights) or self.lb_weights.size == 1
            else self.lb_weights
        )
        self.weights_upper_bound = (
            np.full(self.sample_count, self.ub_weights)
            if np.isscalar(self.ub_weights) or self.ub_weights.size == 1
            else self.ub_weights
        )

        # Prepare controls
        self.controls_constraint = np.maximum(self.control_totals, MIN_CONTROL_VALUE)
        self.controls_importance = np.maximum(
            self.control_importance_weights, MIN_IMPORTANCE
        )

        # Precision
        if self.use_numba and self.numba_precision == "float32":
            self.incidence = self.incidence.astype(np.float32)
            self.initial_weights = self.initial_weights.astype(np.float32)
            self.weights_lower_bound = self.weights_lower_bound.astype(np.float32)
            self.weights_upper_bound = self.weights_upper_bound.astype(np.float32)
            self.controls_constraint = self.controls_constraint.astype(np.float32)
            self.controls_importance = self.controls_importance.astype(np.float32)
            self.max_delta = 1e-5
        else:
            self.max_delta = 1e-8

        # Balancer function
        self.balancer = np_balancer_numba if self.use_numba else np_balancer_py

    def balance(self):
        logger.info(
            "Balancing with Numba=%s, precision=%s",
            self.use_numba,
            self.numba_precision,
        )

        # Process balancing
        weights_final, relaxation_factors, status = self.balancer(
            self.sample_count,
            self.control_count,
            self.master_control_index,
            self.incidence,
            self.initial_weights,
            self.weights_lower_bound,
            self.weights_upper_bound,
            self.controls_constraint,
            self.controls_importance,
            self.max_iterations,
            self.max_delta,
        )

        # Label the status
        status = dict(zip(("converged", "iter", "delta", "max_gamma_dif"), status))

        # weights dataframe
        weights = pd.DataFrame(index=self.incidence_table.index)
        weights["initial"] = self.initial_weights
        weights["final"] = weights_final

        # controls dataframe
        controls = pd.DataFrame(index=self.incidence_table.columns.tolist())
        controls["control"] = np.maximum(self.control_totals, MIN_CONTROL_VALUE)
        controls["relaxation_factor"] = relaxation_factors
        controls["relaxed_control"] = controls.control * relaxation_factors
        controls["weight_totals"] = [
            round((self.incidence_table.loc[:, c] * weights["final"]).sum(), 2)
            for c in controls.index
        ]

        return status, weights, controls


def do_balancing(
    control_spec,
    total_hh_control_col,
    max_expansion_factor,
    min_expansion_factor,
    absolute_upper_bound,
    absolute_lower_bound,
    incidence_df,
    control_totals,
    initial_weights,
    use_hard_constraints,
    use_numba,
    numba_precision,
):

    # incidence table should only have control columns
    incidence_df = incidence_df[control_spec.target]

    # master_control_index is total_hh_control_col
    if total_hh_control_col not in incidence_df.columns:
        raise RuntimeError(
            "total_hh_control column '%s' not found in incidence table"
            % total_hh_control_col
        )
    total_hh_control_index = incidence_df.columns.get_loc(total_hh_control_col)

    # control_totals series rows and incidence_df columns should be aligned
    assert total_hh_control_index == control_totals.index.get_loc(total_hh_control_col)

    control_totals = control_totals.values

    control_importance_weights = control_spec.importance

    if min_expansion_factor:

        # number_of_households in this seed geograpy as specified in seed_controls
        number_of_households = control_totals[total_hh_control_index]

        total_weights = initial_weights.sum()
        lb_ratio = (
            min_expansion_factor * float(number_of_households) / float(total_weights)
        )

        # Added hard limit of min_expansion_factor value that would otherwise drift
        # due to the float(number_of_households) / float(total_weights) calculation
        if use_hard_constraints:
            lb_ratio = np.clip(lb_ratio, a_min=min_expansion_factor, a_max=None)

        lb_weights = initial_weights * lb_ratio

        if absolute_lower_bound:
            lb_weights = lb_weights.clip(lower=absolute_lower_bound)
        else:
            lb_weights = lb_weights.clip(lower=0)

    elif absolute_lower_bound:
        lb_weights = initial_weights.clip(lower=absolute_lower_bound)

    else:
        lb_weights = None

    if max_expansion_factor:

        # number_of_households in this seed geograpy as specified in seed_controlss
        number_of_households = control_totals[total_hh_control_index]

        total_weights = initial_weights.sum()
        ub_ratio = (
            max_expansion_factor * float(number_of_households) / float(total_weights)
        )

        # Added hard limit of max_expansion_factor value that would otherwise drift
        # due to the float(number_of_households) / float(total_weights) calculation
        if use_hard_constraints:
            ub_ratio = np.clip(ub_ratio, a_max=max_expansion_factor, a_min=None)

        ub_weights = initial_weights * ub_ratio

        if absolute_upper_bound:
            ub_weights = (
                ub_weights.round().clip(upper=absolute_upper_bound, lower=1).astype(int)
            )
        else:
            ub_weights = ub_weights.round().clip(lower=1).astype(int)

    elif absolute_upper_bound:
        ub_weights = (
            ub_weights.round().clip(upper=absolute_upper_bound, lower=1).astype(int)
        )

    else:
        ub_weights = None

    max_iterations = setting(
        "MAX_BALANCE_ITERATIONS_SEQUENTIAL", DEFAULT_MAX_ITERATIONS
    )

    balancer = ListBalancer(
        incidence_table=incidence_df,
        initial_weights=initial_weights,
        control_totals=control_totals,
        control_importance_weights=control_importance_weights,
        lb_weights=lb_weights,
        ub_weights=ub_weights,
        master_control_index=total_hh_control_index,
        max_iterations=max_iterations,
        use_numba=use_numba,
        numba_precision=numba_precision,
    )

    status, weights, controls = balancer.balance()

    return status, weights, controls
