from __future__ import annotations

import math

import pandas as pd

from scripts.run_vietnam_tou2026_analysis import (
    build_average_day_dispatch,
    build_case_row,
    build_driver_breakdown,
)


def test_build_case_row_computes_core_deltas() -> None:
    baseline = {
        "year1_dppa_revenue_usd": 100.0,
        "project_irr": 0.10,
        "npv_usd": 1_000.0,
        "year1_grid_savings_usd": 50.0,
    }
    new_case = {
        "year1_dppa_revenue_usd": 80.0,
        "project_irr": 0.08,
        "npv_usd": 700.0,
        "year1_grid_savings_usd": 45.0,
    }

    row = build_case_row(
        case_name="Emivest",
        scenario_name="Option 1",
        baseline=baseline,
        new_case=new_case,
    )

    assert row["case"] == "Emivest"
    assert row["scenario"] == "Option 1"
    assert math.isclose(row["old_revenue_usd"], 150.0)
    assert math.isclose(row["new_revenue_usd"], 125.0)
    assert math.isclose(row["delta_revenue_usd"], -25.0)
    assert math.isclose(row["delta_revenue_pct"], -16.666666666666664)
    assert math.isclose(row["delta_project_irr_pp"], -2.0)
    assert math.isclose(row["delta_npv_usd"], -300.0)


def test_build_driver_breakdown_separates_pv_bess_timing_and_grid() -> None:
    baseline = pd.DataFrame(
        {
            "time_period": ["peak", "peak", "off_peak", "standard"],
            "direct_pv_consumption_kw": [10.0, 0.0, 0.0, 0.0],
            "discharged_kw": [0.0, 6.0, 0.0, 2.0],
            "grid_savings_usd": [3.0, 4.0, 8.0, 5.0],
            "dppa_revenue_usd": [20.0, 9.0, 0.0, 3.0],
        }
    )
    new = pd.DataFrame(
        {
            "time_period": ["standard", "peak", "off_peak", "standard"],
            "direct_pv_consumption_kw": [10.0, 0.0, 0.0, 0.0],
            "discharged_kw": [0.0, 4.0, 0.0, 1.0],
            "grid_savings_usd": [2.0, 4.0, 7.0, 4.0],
            "dppa_revenue_usd": [14.0, 7.0, 0.0, 1.0],
        }
    )

    drivers = build_driver_breakdown(baseline, new)

    assert math.isclose(drivers["Loss of morning peak uplift"], -6.0)
    assert math.isclose(drivers["BESS cycle reduction"], -2.0)
    assert math.isclose(drivers["Shifted peak window (timing)"], -4.0)
    assert math.isclose(drivers["Off-peak rate changes"], -1.0)


def test_build_average_day_dispatch_groups_by_hour() -> None:
    hourly = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    "2026-01-06 00:00:00",
                    "2026-01-06 01:00:00",
                    "2026-01-07 00:00:00",
                    "2026-01-07 01:00:00",
                ]
            ),
            "direct_pv_consumption_kw": [10.0, 0.0, 14.0, 0.0],
            "discharged_kw": [0.0, 6.0, 0.0, 2.0],
            "grid_load_after_re_kw": [50.0, 40.0, 70.0, 20.0],
        }
    )

    average_day = build_average_day_dispatch(hourly)

    assert list(average_day["hour"]) == [0, 1]
    assert math.isclose(float(average_day.loc[0, "solar_direct_kw"]), 12.0)
    assert math.isclose(float(average_day.loc[1, "bess_discharge_kw"]), 4.0)
    assert math.isclose(float(average_day.loc[0, "grid_import_kw"]), 60.0)
