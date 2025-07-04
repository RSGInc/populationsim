# PopulationSim
# See full license in LICENSE.txt.

import logging

import pandas as pd

from populationsim.balancing import do_simul_balancing
from populationsim.integerizing import (
    do_no_integerizing,
    do_simul_integerizing,
    do_sequential_integerizing,
)
from populationsim.core import inject, config
from populationsim.core.helper import (
    get_control_table,
    weight_table_name,
    get_weight_table,
)


logger = logging.getLogger(__name__)


def balance_and_integerize(
    incidence_df,
    parent_weights,
    sub_controls_df,
    control_spec,
    total_hh_control_col,
    parent_geography,
    parent_id,
    sub_geographies,
    crosswalk_df,
    use_numba,
    numba_precision,
):
    """

    Parameters
    ----------
    incidence_df : pandas.Dataframe
        full incidence_df for all hh samples in seed zone
    parent_weights : pandas.Series
        parent zone balanced (possibly integerized) aggregate target weights
    sub_controls_df : pandas.Dataframe
        sub_geography controls (one row per zone indexed by sub_zone id)
    control_spec : pandas.Dataframe
        full control spec with columns 'target', 'seed_table', 'importance', ...
    total_hh_control_col : str
        name of total_hh column (so we can preferentially match this control)
    parent_geography : str
        parent geography zone name
    parent_id : int
        parent geography zone id
    sub_geographies : list(str)
        list of subgeographies in descending order
    crosswalk_df : pandas.Dataframe
        geo crosswork table sliced to current seed geography

    Returns
    -------
    integerized_sub_zone_weights_df : pandas.DataFrame
        canonical form weight table, with columns for 'balanced_weight', 'integer_weight'
        plus columns for household id and sub_geography zone ids
    """
    sub_geography = sub_geographies[0]

    # only want subcontrol rows for current geography geo_id
    sub_ids = crosswalk_df.loc[
        crosswalk_df[parent_geography] == parent_id, sub_geography
    ].unique()
    # only want sub-control rows for this parent geography
    sub_controls_df = sub_controls_df[sub_controls_df.index.isin(sub_ids)]

    # only care about the control columns
    incidence_df = incidence_df[control_spec.target]

    # FIXME - any reason not to just drop out any empty zones?
    empty_sub_zones = sub_controls_df[total_hh_control_col] == 0
    if empty_sub_zones.any():
        logger.info(
            "dropping %s empty %s  in %s %s"
            % (empty_sub_zones.sum(), sub_geography, parent_geography, parent_id)
        )
        sub_controls_df = sub_controls_df[~empty_sub_zones]

    # standard names for sub_control zone columns in controls and weights
    sub_control_zone_names = [
        "%s_%s" % (sub_geography, z) for z in sub_controls_df.index
    ]
    sub_control_zones = pd.Series(sub_control_zone_names, index=sub_controls_df.index)

    balanced_sub_zone_weights, status = do_simul_balancing(
        incidence_df=incidence_df,
        parent_weights=parent_weights,
        sub_controls_df=sub_controls_df,
        control_spec=control_spec,
        total_hh_control_col=total_hh_control_col,
        parent_geography=parent_geography,
        parent_id=parent_id,
        sub_geographies=sub_geographies,
        sub_control_zones=sub_control_zones,
        use_numba=use_numba,
        numba_precision=numba_precision,
    )

    logger.debug(
        "%s %s converged %s iter %s"
        % (parent_geography, parent_id, status["converged"], status["iter"])
    )

    trace_label = "%s_%s" % (parent_geography, parent_id)

    if config.setting("NO_INTEGERIZATION_EVER", False):
        integerizer = do_no_integerizing
        int_method = "no_integerizing"
    elif config.setting("USE_SIMUL_INTEGERIZER", True):
        integerizer = do_simul_integerizing
        int_method = "simul_integerizing"
    else:
        integerizer = do_sequential_integerizing
        int_method = "sequential_integerizing"

    integerized_sub_zone_weights_df = integerizer(
        trace_label=trace_label,
        incidence_df=incidence_df,
        sub_weights=balanced_sub_zone_weights,
        sub_controls_df=sub_controls_df,
        control_spec=control_spec,
        total_hh_control_col=total_hh_control_col,
        sub_geography=sub_geography,
        sub_control_zones=sub_control_zones,
    )

    assert isinstance(
        integerized_sub_zone_weights_df, pd.DataFrame
    ), f"{int_method} did not return a DataFrame"

    integerized_sub_zone_weights_df[parent_geography] = parent_id

    return integerized_sub_zone_weights_df


@inject.step()
def sub_balancing(settings, crosswalk, control_spec, incidence_table):
    """
    Simul-balance and integerize all zones at a specified geographic level
    in groups by parent zone.

    For instance, if the 'geography' step arg is 'TRACT' and the parent geography is 'SEED',
    then for each seed zone, we simul-balance the TRACTS it contains.

    Creates a weight table for the target geography
    with float 'balanced_weight' and 'integer_weight' columns.

    Parameters
    ----------
    settings : dict (settings.yaml as dict)
    crosswalk : pipeline table
    control_spec : pipeline table
    incidence_table : pipeline table

    Returns
    -------

    """

    NO_INTEGERIZATION_EVER = config.setting("NO_INTEGERIZATION_EVER", False)
    SUB_BALANCE_WITH_FLOAT_SEED_WEIGHTS = config.setting(
        "SUB_BALANCE_WITH_FLOAT_SEED_WEIGHTS", True
    )

    # geography is an injected model step arg
    geography = inject.get_step_arg("geography")

    crosswalk_df = crosswalk.to_frame()
    incidence_df = incidence_table.to_frame()
    control_spec = control_spec.to_frame()

    use_numba = settings.get("USE_NUMBA", False)
    numba_precision = settings.get("NUMBA_PRECISION", "float64")

    geographies = settings.get("geographies")
    seed_geography = settings.get("seed_geography")
    meta_geography = geographies[0]
    parent_geography = geographies[geographies.index(geography) - 1]

    sub_geographies = geographies[geographies.index(geography) :]
    parent_geographies = geographies[: geographies.index(geography)]

    total_hh_control_col = config.setting("total_hh_control")

    parent_controls_df = get_control_table(parent_geography)
    sub_controls_df = get_control_table(geography)

    weights_df = get_weight_table(parent_geography)
    assert weights_df is not None

    integer_weights_list = []

    # the incidence table is siloed by seed geography, se we handle each seed zone in turn
    seed_ids = crosswalk_df[seed_geography].unique()
    for seed_num, seed_id in enumerate(seed_ids):

        # slice incidence and crosswalk tables for this seed zone
        seed_incidence_df = incidence_df[incidence_df[seed_geography] == seed_id]
        seed_crosswalk_df = crosswalk_df[crosswalk_df[seed_geography] == seed_id]

        # expects seed geography is siloed by meta_geography
        # (no seed_id is in more than one meta_geography zone)
        assert len(seed_crosswalk_df[meta_geography].unique()) == 1

        # list of unique parent zone ids in this seed zone
        # (there will be just one if parent geography is seed)
        parent_ids = seed_crosswalk_df[parent_geography].unique()

        # only want ones for which there are (non-zero) controls
        parent_ids = parent_controls_df.index.intersection(parent_ids)

        num_parent_ids = len(parent_ids)
        for idx, parent_id in enumerate(parent_ids, start=1):

            logger.info(
                f"balancing {idx}/{num_parent_ids} seed {seed_id} in {seed_num}/{len(seed_ids)}, "
                f"{parent_geography} {parent_id}"
            )

            initial_weights = weights_df[weights_df[parent_geography] == parent_id]
            initial_weights = initial_weights.set_index(
                settings.get("household_id_col")
            )

            # using balanced_weight slows down simul and doesn't improve results
            # (float seeds means no zero-weight households to drop)
            if NO_INTEGERIZATION_EVER or SUB_BALANCE_WITH_FLOAT_SEED_WEIGHTS:
                initial_weights = initial_weights["balanced_weight"]
            else:
                initial_weights = initial_weights["integer_weight"]

            assert len(initial_weights.index) == len(
                seed_incidence_df.index
            ), "seed table and initial weights table do not match, possibly due to overlapping zones in crosswalk."

            zone_weights_df = balance_and_integerize(
                incidence_df=seed_incidence_df,
                parent_weights=initial_weights,
                sub_controls_df=sub_controls_df,
                control_spec=control_spec,
                total_hh_control_col=total_hh_control_col,
                parent_geography=parent_geography,
                parent_id=parent_id,
                sub_geographies=sub_geographies,
                crosswalk_df=seed_crosswalk_df,
                use_numba=use_numba,
                numba_precision=numba_precision,
            )

            # add higher level geography id columns to facilitate summaries
            parent_geography_ids = crosswalk_df.loc[
                crosswalk_df[parent_geography] == parent_id, parent_geographies
            ].max(axis=0)
            for z in parent_geography_ids.index:
                zone_weights_df[z] = parent_geography_ids[z]

            integer_weights_list.append(zone_weights_df)

    integer_weights_df = pd.concat(integer_weights_list)

    logger.info(f"adding table {weight_table_name(geography)}")
    inject.add_table(weight_table_name(geography), integer_weights_df)

    if not NO_INTEGERIZATION_EVER:

        inject.add_table(
            weight_table_name(geography, sparse=True),
            integer_weights_df[integer_weights_df["integer_weight"] > 0],
        )

    if "trace_geography" in settings and geography in settings["trace_geography"]:
        trace_geography_id = settings.get("trace_geography")[geography]
        df = integer_weights_df[integer_weights_df[geography] == trace_geography_id]
        inject.add_table("trace_%s" % weight_table_name(geography), df)
