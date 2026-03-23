"""
Maintenance Reserve Account (MRA) schedule.

Models the annual cash outflows for building up the BESS and PV maintenance
reserves from Year 1 onward. Year 0 equity-at-financial-close funding is
excluded from the returned operating-year series.

Excel source: Financial!F98–F103, Assumption!K46–K47, Other Input!B5–B8
"""

from __future__ import annotations

import pandas as pd


_DEFAULT_BUILDUP: dict[int, float] = {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25}


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

    BESS MRA target = 60% of BESS CAPEX, funded evenly over years 1–4 (15%/yr).
    PV MRA target   = 10% of PV CAPEX,   funded evenly over years 1–4 (2.5%/yr).
    Both targets are 25% of their respective reserves per operating year.

    Excel source:
        BESS MRA target = Assumption!K46 × BESS CAPEX  (default 60%)
        PV MRA target   = Assumption!K47 × PV CAPEX    (default 10%)
        Build-up        = Other Input!B5–B8 (years 1–4, each 25% of target)

    Args:
        bess_capex_usd: BESS capital cost (USD).
        pv_capex_usd: PV capital cost (USD).
        bess_mra_pct: BESS MRA as fraction of BESS CAPEX (K46, default 60%).
        pv_mra_pct: PV MRA as fraction of PV CAPEX (K47, default 10%).
        buildup_schedule: Dict {year: fraction_of_target} for operating years.
            Defaults to {1: 25%, 2: 25%, 3: 25%, 4: 25%} (100% over 4 years).
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
        total_target * buildup_schedule.get(year, 0.0) for year in range(1, project_years + 1)
    ]
    return pd.Series(
        contributions,
        index=pd.RangeIndex(1, project_years + 1),
        name="mra_contribution_usd",
    )
