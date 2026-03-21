"""
OPEX schedule construction.

Computes annual operating expense line items (O&M, insurance, asset
management, land lease) from unit-rate inputs, applying compound
escalation over the project lifetime.

Excel source: Financial!F106–F113, Assumption!K26–K34
"""

from __future__ import annotations

import pandas as pd


def build_opex_schedule(
    solar_capacity_mwp: float,
    bess_capacity_mwh: float,
    total_capex_usd: float,
    project_years: int = 25,
    cpi: float = 0.04,
    om_solar_usd_per_mwp: float = 8_000.0,
    om_bess_usd_per_mwh: float = 5_000.0,
    insurance_pct_capex: float = 0.005,
    asset_management_usd: float = 15_000.0,
    land_lease_usd: float = 20_000.0,
) -> pd.DataFrame:
    """
    Build annual OPEX schedule with compound CPI escalation.

    Year 1 base values are computed from unit rates. Each subsequent year
    applies compound escalation: value_yr_n = value_yr1 × (1 + cpi)^(n-1).

    Excel source:
        O&M Solar       = om_solar_usd_per_mwp × solar_capacity_mwp
        O&M BESS        = om_bess_usd_per_mwh  × bess_capacity_mwh
        Insurance       = insurance_pct_capex × total_capex_usd
        Asset Mgmt      = asset_management_usd  (flat annual fee)
        Land Lease      = land_lease_usd         (flat annual fee)
        OPEX Escalation = cpi (Assumption!K34, default 4%)

    Args:
        solar_capacity_mwp: Installed PV capacity (MWp).
        bess_capacity_mwh: Total BESS storage capacity (MWh).
        total_capex_usd: Total project CAPEX (USD).
        project_years: Number of years in the projection.
        cpi: Annual OPEX escalation rate (default 4%).
        om_solar_usd_per_mwp: O&M cost for solar (USD/MWp/yr, default $8,000).
        om_bess_usd_per_mwh: O&M cost for BESS (USD/MWh/yr, default $5,000).
        insurance_pct_capex: Insurance as fraction of total CAPEX (default 0.5%).
        asset_management_usd: Flat annual asset management fee (USD, default $15,000).
        land_lease_usd: Flat annual land lease fee (USD, default $20,000).

    Returns:
        DataFrame with OPEX_COLUMNS schema, indexed by year (1-based).
        Columns: year, o_and_m_usd, insurance_usd, land_lease_usd,
                 management_fees_usd, grid_connection_usd, taxes_usd,
                 mra_contribution_usd.
    """
    om_base = (
        om_solar_usd_per_mwp * solar_capacity_mwp
        + om_bess_usd_per_mwh * bess_capacity_mwh
    )
    insurance_base = insurance_pct_capex * total_capex_usd
    land_lease_base = land_lease_usd
    management_base = asset_management_usd

    years = list(range(1, project_years + 1))
    rows: list[dict] = []
    for year in years:
        esc = (1.0 + cpi) ** (year - 1)
        rows.append(
            {
                "year": year,
                "o_and_m_usd": om_base * esc,
                "insurance_usd": insurance_base * esc,
                "land_lease_usd": land_lease_base * esc,
                "management_fees_usd": management_base * esc,
                "grid_connection_usd": 0.0,
                "taxes_usd": 0.0,
                "mra_contribution_usd": 0.0,
            }
        )

    df = pd.DataFrame(rows)
    return df.set_index("year", drop=False)
