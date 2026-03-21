"""
PPA revenue mode enumeration and central dispatcher.

This module provides the ``PpaMode`` enum that names the four revenue
scenarios available in the Excel model (``Assumption!Q20``), plus a
single ``calculate_revenue`` dispatcher that routes hourly data to the
correct settlement sub-module.

Excel source:
    Assumption!Q20 — active PPA option (1-4)
    Financial!F64–F90 — per-option hourly revenue logic

Usage::

    from re_storage.settlement.revenue import PpaMode, calculate_revenue

    revenue_series = calculate_revenue(
        mode=PpaMode.DPPA_CFD,
        hourly_data=hourly_df,
        assumptions=sys_assumptions,
        tariff_rates=rates,
    )
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any

import pandas as pd

from re_storage.core.types import TimePeriod
from re_storage.inputs.schemas import SystemAssumptions
from re_storage.settlement.bundled import calculate_bundled_revenue
from re_storage.settlement.dppa import calculate_dppa_revenue
from re_storage.settlement.fixed_ppa import calculate_fixed_ppa_revenue
from re_storage.settlement.separate import calculate_separate_revenue


class PpaMode(IntEnum):
    """
    PPA revenue scenario selector.

    Mirrors ``Assumption!Q20`` in the Excel model.  The integer values
    are intentionally identical to the Excel option numbers so that
    ``PpaMode(int_from_excel)`` always produces the correct member.

    Members
    -------
    BUNDLED_DISCOUNT:
        Option 1 — single blended rate = EVN off-peak tariff × (1 – discount%).
        Solar and BESS revenue are bundled together.
        Key parameter: ``bundled_discount_pct`` (default 15 %).
    SEPARATE_PV_BESS:
        Option 2 — PV energy sold at ``pv_discount_pct`` off the EVN tariff;
        BESS discharge sold separately at ``bess_discount_pct`` off the tariff.
    DPPA_CFD:
        Option 3 — DPPA with Contract-for-Difference settlement.
        Market revenue plus CfD top-up/clawback against a strike price.
        This is the **default** option and the only one originally
        implemented in the Python package.
    FIXED_PPA:
        Option 4 — fixed price per kWh for all exported energy.
        No market reference, no CfD settlement.
        Key parameter: ``fixed_ppa_price_usd_per_mwh`` (default $70/MWh).
    """

    BUNDLED_DISCOUNT = 1
    SEPARATE_PV_BESS = 2
    DPPA_CFD = 3
    FIXED_PPA = 4

    @classmethod
    def from_excel_option(cls, option: int) -> "PpaMode":
        """
        Construct a ``PpaMode`` from an integer read from ``Assumption!Q20``.

        Args:
            option: Integer option value (1-4).

        Returns:
            Corresponding ``PpaMode`` member.

        Raises:
            ValueError: If ``option`` is not in {1, 2, 3, 4}.
        """
        try:
            return cls(option)
        except ValueError:
            valid = [m.value for m in cls]
            raise ValueError(
                f"Excel PPA option must be one of {valid}, got {option!r}."
            ) from None


def calculate_revenue(
    mode: PpaMode | int,
    hourly_data: pd.DataFrame,
    assumptions: SystemAssumptions,
    tariff_rates: dict[TimePeriod, float],
) -> pd.DataFrame:
    """
    Dispatch hourly revenue calculation to the correct PPA sub-module.

    This is the single entry-point for all four PPA revenue scenarios.
    Callers provide a ``PpaMode`` (or the raw integer option number) and
    the function returns the ``hourly_data`` DataFrame with a
    ``dppa_revenue_usd`` column appended (using the standard column name
    so that downstream aggregation stages remain unchanged).

    For Options 1, 2, and 4 only ``dppa_revenue_usd`` is added.
    For Option 3 (DPPA CfD) the full set of intermediate DPPA columns is
    also added (``delivered_re_kwh``, ``consumed_re_kwh``,
    ``market_revenue_usd``, ``cfd_settlement_usd``,
    ``total_dppa_revenue_usd``).

    Args:
        mode: PPA scenario selector.  Accepts ``PpaMode`` members *or*
            a raw ``int`` (1-4) so that pipeline code that reads the
            option directly from the loader dict can call this function
            without an explicit conversion.
        hourly_data: Hourly time series DataFrame.  Must contain at least:
            - ``direct_pv_consumption_kw`` — direct PV to load (kW)
            - ``discharged_kw`` — BESS discharge to load (kW)
            - ``solar_gen_kw`` — total solar generation (kW)
            - ``time_period`` — tariff period classification
            For DPPA (Option 3) also: ``net_gen_for_dppa_kwh``,
            ``load_kwh``, ``fmp_usd_per_kwh``.
        assumptions: System assumptions including all PPA parameters
            (``bundled_discount_pct``, ``pv_discount_pct``,
            ``bess_discount_pct``, ``fixed_ppa_price_usd_per_mwh``,
            ``strike_price_usd_per_kwh``, …).
        tariff_rates: Dict mapping ``TimePeriod`` → rate (USD/kWh).
            Used by Options 1 and 2; ignored by Options 3 and 4.

    Returns:
        A **new** DataFrame (copy of ``hourly_data``) with the revenue
        column(s) appended.  The column ``dppa_revenue_usd`` is always
        present and is the canonical hourly revenue signal consumed by
        ``aggregation.annual`` and ``aggregation.lifetime``.

    Raises:
        ValueError: If ``mode`` is not a valid ``PpaMode`` value.

    Examples::

        >>> rev_df = calculate_revenue(
        ...     mode=PpaMode.BUNDLED_DISCOUNT,
        ...     hourly_data=hourly_df,
        ...     assumptions=assumptions,
        ...     tariff_rates=rates,
        ... )
        >>> rev_df["dppa_revenue_usd"].sum()
        1_234_567.89

        >>> # Integer option numbers also accepted
        >>> rev_df = calculate_revenue(3, hourly_df, assumptions, rates)
    """
    # Normalise to enum
    if not isinstance(mode, PpaMode):
        mode = PpaMode.from_excel_option(int(mode))

    result = hourly_data.copy()

    if mode is PpaMode.BUNDLED_DISCOUNT:
        # Option 1 — single blended rate for all delivered energy
        result["dppa_revenue_usd"] = calculate_bundled_revenue(
            direct_pv_kw=result["direct_pv_consumption_kw"],
            discharged_kw=result["discharged_kw"],
            time_period=result["time_period"],
            tariff_rates=tariff_rates,
            discount_pct=assumptions.bundled_discount_pct,
        )

    elif mode is PpaMode.SEPARATE_PV_BESS:
        # Option 2 — independent discount rates for PV vs BESS
        result["dppa_revenue_usd"] = calculate_separate_revenue(
            direct_pv_kw=result["direct_pv_consumption_kw"],
            discharged_kw=result["discharged_kw"],
            time_period=result["time_period"],
            tariff_rates=tariff_rates,
            pv_discount_pct=assumptions.pv_discount_pct,
            bess_discount_pct=assumptions.bess_discount_pct,
        )

    elif mode is PpaMode.FIXED_PPA:
        # Option 4 — fixed $/MWh price, no market reference
        result["dppa_revenue_usd"] = calculate_fixed_ppa_revenue(
            solar_gen_kw=result["solar_gen_kw"],
            fixed_price_usd_per_mwh=assumptions.fixed_ppa_price_usd_per_mwh,
        )

    else:
        # Option 3 (default) — DPPA with CfD settlement
        # calculate_dppa_revenue appends multiple columns including
        # total_dppa_revenue_usd; we alias it to dppa_revenue_usd for
        # consistency with the other options.
        result = calculate_dppa_revenue(result, assumptions)
        if "dppa_revenue_usd" not in result.columns:
            result["dppa_revenue_usd"] = result["total_dppa_revenue_usd"]

    return result
