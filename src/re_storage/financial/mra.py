"""
Maintenance Reserve Account (MRA) schedule.

Models the annual cash outflows for building up the BESS and PV maintenance
reserves from Year 1 through Year 3 (Year 0 contribution is equity at FC).

Excel source: Financial!F98–F103, Assumption!K46–K47, Other Input!B5–B8
"""

from __future__ import annotations

import pandas as pd


_DEFAULT_BUILDUP: dict[int, float] = {0: 0.10, 1: 0.30, 2: 0.30, 3: 0.30}


def build_mra_schedule(
    bess_capex_usd: float,
    pv_capex_usd: float,
    bess_mra_pct: float = 0.60,
    pv_mra_pct: float = 0.10,
    buildup_schedule: dict[int, float] | None = None,
    project_years: int = 25,
) -> pd.Series:
    """
    Build annual MRA contribution schedule (operating years 1+).

    The Year 0 contribution (10% of target) is funded as equity at financial
    close and is handled by the equity injection in the waterfall. This
    function returns only the operating-year contributions (years 1–N).

    Excel source:
        BESS MRA target = Assumption!K46 × BESS CAPEX  (default 60%)
        PV MRA target   = Assumption!K47 × PV CAPEX    (default 10%)
        Build-up        = Other Input!B5–B8 (Years 0–3, summing to 100%)

    Args:
        bess_capex_usd: BESS capital cost (USD).
        pv_capex_usd: PV capital cost (USD).
        bess_mra_pct: BESS MRA as fraction of BESS CAPEX (K46, default 60%).
        pv_mra_pct: PV MRA as fraction of PV CAPEX (K47, default 10%).
        buildup_schedule: Dict {year: fraction_of_target} for years 0–3.
            Defaults to {0: 10%, 1: 30%, 2: 30%, 3: 30%}.
        project_years: Total project years for the output series.

    Returns:
        Series of annual MRA contributions (USD) for years 1–project_years,
        indexed by year (1-based).
    """
    if buildup_schedule is None:
        buildup_schedule = _DEFAULT_BUILDUP

    bess_target = bess_mra_pct * bess_capex_usd
    pv_target = pv_mra_pct * pv_capex_usd
    total_target = bess_target + pv_target

    contributions = [
        total_target * buildup_schedule.get(year, 0.0)
        for year in range(1, project_years + 1)
    ]
    return pd.Series(
        contributions,
        index=pd.RangeIndex(1, project_years + 1),
        name="mra_contribution_usd",
    )
