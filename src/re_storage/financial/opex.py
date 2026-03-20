"""
OPEX schedule construction.

Computes annual operating expense line items (O&M, insurance, asset
management, land lease, other) from unit-rate inputs, applying compound
escalation over the project lifetime.

Excel source: Financial!F106–F113, Assumption!K26–K34
"""

from __future__ import annotations

import pandas as pd


def build_opex_schedule(
    project_years: int,
    installed_pv_mwp: float,
    bess_mwh: float,
    total_capex_usd: float,
    om_solar_usd_per_mwp: float = 6_000.0,
    om_bess_usd_per_mwh: float = 2_000.0,
    insurance_solar_pct_capex: float = 0.0025,
    insurance_bess_pct_capex: float = 0.0025,
    other_opex_usd_per_mwp: float = 1_000.0,
    asset_management_usd_per_mwp: float = 3_000.0,
    land_lease_pct_revenue: float = 0.0,
    opex_escalation_pct: float = 0.04,
    year1_total_revenue_usd: float = 0.0,
) -> pd.DataFrame:
    """
    Build annual OPEX schedule with compound escalation.

    Year 1 base values are computed from unit rates. Each subsequent year
    applies compound escalation: value_yr_n = value_yr1 × (1 + esc)^(n-1).

    Excel source:
        O&M Solar       = K26 × installed_mwp
        O&M BESS        = K27 × bess_mwh
        Insurance       = (K29 + K30) × total_capex
        Other Opex      = K31 × installed_mwp
        Asset Mgmt      = K32 × installed_mwp
        Land Lease      = K33 × year1_revenue
        OPEX Escalation = K34

    Args:
        project_years: Number of years in the projection.
        installed_pv_mwp: Installed PV capacity (MWp).
        bess_mwh: Total BESS storage capacity (MWh).
        total_capex_usd: Total project CAPEX (USD).
        om_solar_usd_per_mwp: O&M cost for solar (USD/MWp/yr, Assumption!K26).
        om_bess_usd_per_mwh: O&M cost for BESS (USD/MWh/yr, Assumption!K27).
        insurance_solar_pct_capex: Solar insurance as fraction of CAPEX (K29).
        insurance_bess_pct_capex: BESS insurance as fraction of CAPEX (K30).
        other_opex_usd_per_mwp: Other OPEX per MWp/yr (Assumption!K31).
        asset_management_usd_per_mwp: Asset management per MWp/yr (K32).
        land_lease_pct_revenue: Land lease as fraction of annual revenue (K33).
        opex_escalation_pct: Annual OPEX escalation rate (K34, default 4%).
        year1_total_revenue_usd: Year 1 total revenue for land lease calculation.

    Returns:
        DataFrame with OPEX_COLUMNS schema, indexed by year (1-based).
        Columns: year, o_and_m_usd, insurance_usd, land_lease_usd,
                 management_fees_usd, grid_connection_usd, taxes_usd,
                 mra_contribution_usd.
    """
    om_base = (
        om_solar_usd_per_mwp * installed_pv_mwp
        + om_bess_usd_per_mwh * bess_mwh
        + other_opex_usd_per_mwp * installed_pv_mwp
    )
    insurance_base = (insurance_solar_pct_capex + insurance_bess_pct_capex) * total_capex_usd
    land_lease_base = land_lease_pct_revenue * year1_total_revenue_usd
    management_base = asset_management_usd_per_mwp * installed_pv_mwp

    years = list(range(1, project_years + 1))
    rows: list[dict] = []
    for year in years:
        esc = (1.0 + opex_escalation_pct) ** (year - 1)
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
