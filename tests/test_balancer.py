# PopulationSim
# See full license in LICENSE.txt.

import numpy as np
import pandas as pd
import numpy.testing as npt
import pytest
import time

from populationsim.balancing import ListBalancer, do_balancing
from populationsim.balancing.balancers import (
    np_balancer_py,
    np_simul_balancer_py,
)
from populationsim.balancing.balancers_numba import (
    np_balancer_numba,
    np_simul_balancer_numba,
)
from populationsim.balancing.constants import (
    DEFAULT_MAX_ITERATIONS,
    MIN_CONTROL_VALUE,
)
from populationsim.core import inject


@pytest.mark.parametrize("use_numba", [True, False])
def test_Konduri(use_numba):

    # example from Konduri et al. "Enhanced Synthetic Population Generator..."
    # Journal of the Transportation Research Board, No. 2563

    # rows are elements for which factors are calculated, columns are constraints to be satisfied
    incidence_table = pd.DataFrame(
        {
            "hh_1": [1, 1, 1, 0, 0, 0, 0, 0],
            "hh_2": [0, 0, 0, 1, 1, 1, 1, 1],
            "p1": [1, 1, 2, 1, 0, 1, 2, 1],
            "p2": [1, 0, 1, 0, 2, 1, 1, 1],
            "p3": [1, 1, 0, 2, 1, 0, 2, 0],
        }
    )

    # one weight per row in incidence table
    initial_weights = np.asanyarray([1, 1, 1, 1, 1, 1, 1, 1])

    # column totals which the final weighted incidence table sums must satisfy
    control_totals = [35, 65, 91, 65, 104]

    # one for every column in incidence_table
    control_importance_weights = [100000] * len(control_totals)

    balancer = ListBalancer(
        incidence_table=incidence_table,
        initial_weights=initial_weights,
        control_totals=control_totals,
        control_importance_weights=control_importance_weights,
        lb_weights=0,
        ub_weights=30,
        master_control_index=None,
        max_iterations=DEFAULT_MAX_ITERATIONS,
        use_numba=use_numba,
        numba_precision="float32",
    )

    status, weights, controls = balancer.balance()

    weighted_sum = [
        round((incidence_table.loc[:, c] * weights.final).sum(), 2)
        for c in controls.index
    ]

    published_final_weights = [1.36, 25.66, 7.98, 27.79, 18.45, 8.64, 1.47, 8.64]
    published_weighted_sum = [
        round((incidence_table.loc[:, c] * published_final_weights).sum(), 2)
        for c in controls.index
    ]
    npt.assert_almost_equal(weighted_sum, published_weighted_sum, decimal=1)

    npt.assert_almost_equal(weighted_sum, controls["control"], decimal=1)
    assert status["converged"]


def test_hard_constraints_cap_average_seed_expansion():
    """Reproduce issue #221's expected hard cap interpretation."""
    inject.clear_cache()
    inject.add_injectable("settings", {})

    household_count = 100
    target_households = 5100.0
    max_expansion_factor = 50
    expected_max_weight = target_households / household_count * max_expansion_factor

    # The high initial survey weight represents the issue pattern: total survey
    # weights are calibrated to the target total, but one record has a large
    # starting weight. Current code caps this record at initial_weight * 50.
    high_initial_weight = 1078.0
    remaining_initial_weight = target_households - high_initial_weight
    initial_weights = pd.Series(
        [high_initial_weight]
        + [remaining_initial_weight / (household_count - 1)] * (household_count - 1)
    )

    incidence_table = pd.DataFrame(
        {
            "num_hh": np.ones(household_count),
            "rare_hh_type": [1] + [0] * (household_count - 1),
        }
    )
    control_spec = pd.DataFrame(
        {
            "target": ["num_hh", "rare_hh_type"],
            "importance": [1e9, 1e9],
        }
    )
    control_totals = pd.Series({"num_hh": target_households, "rare_hh_type": 3000.0})

    status, weights, _ = do_balancing(
        control_spec=control_spec,
        total_hh_control_col="num_hh",
        max_expansion_factor=max_expansion_factor,
        min_expansion_factor=None,
        absolute_upper_bound=None,
        absolute_lower_bound=None,
        incidence_df=incidence_table,
        control_totals=control_totals,
        initial_weights=initial_weights,
        use_hard_constraints=True,
        use_numba=False,
        numba_precision="float64",
    )

    assert status["converged"]
    assert weights["final"].max() <= expected_max_weight


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_balancer_compare_numba_vs_py(dtype):
    np.random.seed(42)

    sample_count = 1000
    control_count = 100
    iterations = DEFAULT_MAX_ITERATIONS
    status_labs = ("converged", "iter", "delta", "max_gamma_dif")

    incidence = np.random.rand(control_count, sample_count)
    weights_initial = np.ones(sample_count)
    weights_lower_bound = np.full(sample_count, MIN_CONTROL_VALUE)
    weights_upper_bound = np.full(sample_count, 1 / MIN_CONTROL_VALUE)
    controls_constraint = np.random.uniform(1000, 5000, control_count)
    controls_importance = np.random.uniform(0.5, 2.0, control_count)
    master_control_index = -1

    # Warm up Numba to exclude compilation time from the first run
    print("\nWarming up Numba...")
    np_balancer_numba(
        sample_count,
        control_count,
        master_control_index,
        incidence,
        weights_initial,
        weights_lower_bound,
        weights_upper_bound,
        controls_constraint,
        controls_importance,
        2,
    )

    print("Running Numba version...")
    # --- Run Numba version ---
    start_numba = time.perf_counter()
    w_numba, r_numba, s_numba = np_balancer_numba(
        sample_count,
        control_count,
        master_control_index,
        incidence.astype(dtype),
        weights_initial.astype(dtype),
        weights_lower_bound.astype(dtype),
        weights_upper_bound.astype(dtype),
        controls_constraint.astype(dtype),
        controls_importance.astype(dtype),
        iterations,
    )
    duration_numba = time.perf_counter() - start_numba
    s_numba = dict(zip(status_labs, s_numba))
    print(
        f"Numba: {duration_numba:.4f}s, Iter: {s_numba['iter']}, Converged: {s_numba['converged']}"
    )

    # --- Run Python version ---
    start_py = time.perf_counter()
    w_py, r_py, s_py = np_balancer_py(
        sample_count,
        control_count,
        master_control_index,
        incidence,
        weights_initial,
        weights_lower_bound,
        weights_upper_bound,
        controls_constraint,
        controls_importance,
        iterations,
    )
    duration_py = time.perf_counter() - start_py
    s_py = dict(zip(status_labs, s_py))
    print(
        f"Python: {duration_py:.4f}s, Iter: {s_py['iter']}, Converged: {s_py['converged']}"
    )

    print(f"Speedup: {(duration_py / duration_numba):.2f}x")

    # --- Assertions ---
    assert np.allclose(w_numba, w_py, rtol=1e-4, atol=1e-6), "Weights mismatch"
    assert s_numba["converged"], "Numba version did not converge"
    assert s_py["converged"], "Python version did not converge"
    # assert duration_numba < duration_py * 0.5, "Numba version not at least 2x faster"


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_simul_balancer_compare_numba_vs_py(dtype):

    np.random.seed(42)

    sample_count = 100
    control_count = 9
    zone_count = 3
    iterations = DEFAULT_MAX_ITERATIONS
    status_labs = ("converged", "iter", "delta", "max_gamma_dif")

    # Simul data
    incidence = np.random.rand(control_count, sample_count)
    sub_weights = np.random.rand(zone_count, sample_count)
    weights_lower_bound = np.full(sample_count, MIN_CONTROL_VALUE)
    weights_upper_bound = np.full(sample_count, 1 / MIN_CONTROL_VALUE)
    controls_importance = np.random.uniform(0.5, 2.0, control_count)
    sub_controls = np.random.uniform(500, 2000, (zone_count, control_count))
    parent_weights = np.random.uniform(5000, 10000, sample_count)
    parent_controls = np.random.uniform(1000, 5000, control_count)
    master_control_index = -1

    print("\nWarming up Numba...")
    np_simul_balancer_numba(
        sample_count,
        control_count,
        zone_count,
        master_control_index,
        incidence,
        parent_weights,
        weights_lower_bound,
        weights_upper_bound,
        sub_weights,
        parent_controls,
        controls_importance,
        sub_controls,
        2,
    )

    print("Running Numba version...")
    start_numba = time.perf_counter()
    w_numba, r_numba, s_numba = np_simul_balancer_numba(
        sample_count,
        control_count,
        zone_count,
        master_control_index,
        incidence.astype(dtype),
        parent_weights.astype(dtype),
        weights_lower_bound.astype(dtype),
        weights_upper_bound.astype(dtype),
        sub_weights.astype(dtype),
        parent_controls.astype(dtype),
        controls_importance.astype(dtype),
        sub_controls.astype(dtype),
        iterations,
    )
    duration_numba = time.perf_counter() - start_numba
    s_numba = dict(zip(status_labs, s_numba))
    print(
        f"Numba: {duration_numba:.4f}s, Iter: {s_numba['iter']}, Converged: {s_numba['converged']}"
    )

    print("Running Python version...")
    start_py = time.perf_counter()
    w_py, r_py, s_py = np_simul_balancer_py(
        sample_count,
        control_count,
        zone_count,
        master_control_index,
        incidence,
        parent_weights,
        weights_lower_bound,
        weights_upper_bound,
        sub_weights,
        parent_controls,
        controls_importance,
        sub_controls,
        iterations,
    )
    duration_py = time.perf_counter() - start_py
    s_py = dict(zip(status_labs, s_py))
    print(
        f"Python: {duration_py:.4f}s, Iter: {s_py['iter']}, Converged: {s_py['converged']}"
    )

    print(f"Speedup: {duration_py / duration_numba:.2f}x")

    # --- Assertions ---
    assert np.allclose(w_numba, w_py, rtol=1e-4, atol=1e-6), "Weights mismatch"
    assert s_numba["converged"], "Numba version did not converge"
    assert s_py["converged"], "Python version did not converge"
    # assert duration_numba < duration_py, "Numba version not at least 1x faster"
