"""Helpers for building JSON-model payloads from multipart form data."""

from __future__ import annotations

import json
from typing import Any

# Tariff modes accepted by the model pipeline. Keep aligned with
# ``re_storage.pipeline.VALID_TARIFF_MODES`` - both must accept these.
VALID_TARIFF_MODES = {"1-component", "2-component"}


def to_float(form: dict[str, str], key: str, default: float) -> float:
    raw = form.get(key)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def to_int(form: dict[str, str], key: str, default: int) -> int:
    raw = form.get(key)
    if raw is None or raw.strip() == "":
        return default
    return int(float(raw))


def to_bool(form: dict[str, str], key: str, default: bool) -> bool:
    raw = form.get(key)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def to_str(form: dict[str, str], key: str, default: str) -> str:
    raw = form.get(key)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip()


def resolve_tariff_mode(form: dict[str, str]) -> str:
    """Read ``tariff_mode`` from the form and validate against the pipeline.

    Returns the validated mode (default ``"1-component"``). Raises
    ``ValueError`` for anything outside :data:`VALID_TARIFF_MODES` so handlers
    can return a 400 to the client.
    """
    mode = to_str(form, "tariff_mode", "1-component")
    if mode not in VALID_TARIFF_MODES:
        raise ValueError(
            f"tariff_mode must be one of {sorted(VALID_TARIFF_MODES)}, got {mode!r}"
        )
    return mode


def build_project_payload(form: dict[str, str]) -> dict[str, Any]:
    actual_capacity_kwp = to_float(form, "actual_capacity_kwp", 0.0)
    simulation_capacity_kwp = to_float(form, "simulation_capacity_kwp", actual_capacity_kwp)
    total_bess_kwh = to_float(form, "total_bess_kwh", 0.0)
    half_cycle_efficiency = to_float(form, "half_cycle_efficiency", 0.95)
    connection_voltage_kv = to_float(form, "connection_voltage_kv", 22.0)
    exchange_rate = to_float(form, "exchange_rate_usd_vnd", 26000.0)
    strike_price_vnd = to_float(form, "strike_price_vnd", 1800.0)
    kpp_22 = to_float(form, "kpp_22", 1.027263)
    kpp_110 = to_float(form, "kpp_110", 1.008525)
    project_years = to_int(form, "project_years", 20)
    ppa_option = to_int(form, "ppa_option", 3)

    tariff_mode = resolve_tariff_mode(form)
    cp_demand_vnd = to_float(form, "cp_demand_vnd_per_kw", 0.0)

    degradation_json = form.get("degradation_json", "")
    if degradation_json.strip() == "":
        annual_table = [
            {
                "year": year,
                "pv_retention": max(1.0 - 0.005 * (year - 1), 0.8),
                "battery_retention": max(1.0 - 0.02 * (year - 1), 0.5),
                "battery_with_replacement": max(1.0 - 0.015 * (year - 1), 0.6),
            }
            for year in range(1, project_years + 1)
        ]
    else:
        parsed = json.loads(degradation_json)
        if not isinstance(parsed, list):
            raise ValueError("degradation_json must be a JSON array")
        annual_table = parsed

    return {
        "project": form.get("project_name", "Web Project"),
        "model": "Solar + BESS Techno-Economic Model",
        "developer": "RE-Storage Web Tool",
        "system_input": {
            "actual_installation_capacity_kWp": actual_capacity_kwp,
            "simulation_capacity_kWp": simulation_capacity_kwp,
            "bess_included": to_bool(form, "bess_enabled", True),
        },
        "bess_parameters": {
            "total_bess_storage_capacity_kWh": total_bess_kwh,
            "total_bess_power_output_kW": to_float(form, "bess_power_rating_kw", 0.0),
            "depth_of_discharge_pct": to_float(form, "dod", 0.85),
            "half_cycle_efficiency_pct": half_cycle_efficiency,
        },
        "bess_operation_strategy": {
            "strategy_mode": to_int(form, "strategy_mode", 1),
            "charge": {
                "solar_active_charging": {
                    "pv2bess_pre_charge_mode": to_int(form, "charging_mode", 1),
                    "pre_charge_share_of_pv_1_pct": to_float(form, "active_pv2bess_share", 0.3),
                    "pre_charge_start_hour_1": to_int(form, "charge_start_hour", 10),
                    "pre_charge_end_hour_1": to_int(form, "charge_end_hour", 16),
                    "min_pv_directly_to_load_pct": to_float(form, "min_direct_pv_share", 0.1),
                    "precharge_target_soc_kWh_2": to_float(
                        form,
                        "precharge_target_soc_kwh",
                        max(total_bess_kwh * to_float(form, "dod", 0.85), 0.0),
                    ),
                    "precharge_target_hour_2": to_int(form, "precharge_target_hour", 17),
                }
            },
        },
        "financial_input": {
            "exchange_rate_USD_VND": exchange_rate,
            "timing": {
                "financial_close_excel_serial": to_int(form, "financial_close_serial", 46022),
                "commercial_operation_date_excel_serial": to_int(form, "cod_excel_serial", 46023),
                "project_lifetime_years": project_years,
            },
        },
        "grid_connection_and_tariff": {
            "connection_voltage_level_kV": connection_voltage_kv,
            "tariff_structure": tariff_mode,
            "evn_retail_tariff_VND": {
                "Cp_demand": cp_demand_vnd,
                "Ca_normal": to_float(form, "evn_tariff_standard_vnd", 1833.0),
                "Ca_peak": to_float(form, "evn_tariff_peak_vnd", 3398.0),
                "Ca_offpeak": to_float(form, "evn_tariff_off_peak_vnd", 1190.0),
            },
            "current_applied_evn_tariff_USD_MWh": {
                "off_peak": to_float(form, "tariff_off_peak", 45.7692307692308),
                "standard": to_float(form, "tariff_standard", 70.5),
                "peak": to_float(form, "tariff_peak", 130.692307692308),
                "capacity": 0.0,
            },
        },
        "ppa_settings": {
            "contract_duration_years": project_years,
            "active_ppa_option": ppa_option,
            "option_3_dppa": {
                "model_active": to_bool(form, "dppa_enabled", True),
                "strike_price_VND": strike_price_vnd,
                "avg_sun_hours_market_price_descent_pct_pa": to_float(
                    form,
                    "fmp_descent_pct",
                    -0.05,
                ),
                "curtailment_pct": to_float(form, "dppa_curtailment_pct", 0.02),
                "price_escalation_pct": to_float(form, "revenue_escalation_pct", 0.05),
                "regulation_parameters": {
                    "k": to_float(form, "k_factor", 1.02),
                    "Kpp_22kv": kpp_22,
                    "Kpp_110kv": kpp_110,
                },
            },
            "option_1_corporate_buyer": {
                "evn_price_escalation_pct_pa": to_float(form, "revenue_escalation_pct", 0.05),
                "net_billing_USD_MWh": to_float(form, "net_billing_usd_per_mwh", 38.4615384615385),
                "pv_export_net_billing_share_pct": to_float(
                    form, "net_billing_export_share_pct", 0.2
                ),
                "bundled_discount_to_evn_tariff_pct": to_float(form, "bundled_discount_pct", 0.15),
            },
            "option_2_pv_bess_discount": {
                "pv_discount_to_evn_tariff_pct": to_float(form, "pv_discount_pct", 0.05),
                "bess_discount_to_evn_tariff_pct": to_float(form, "bess_discount_pct", 0.05),
            },
            "option_4_ppa_with_evn": {
                "all_in_fixed_price_USD_MWh": to_float(form, "fixed_ppa_price_usd_per_mwh", 70.0),
                "curtailment_pct": to_float(form, "fixed_ppa_curtailment_pct", 0.03),
                "transmission_loss_pct": to_float(form, "fixed_ppa_tx_loss_pct", 0.01),
            },
        },
        "capex": {
            "land_acquisition_USD": to_float(form, "land_acquisition_usd", 0.0),
            "solar_USD_per_MWp": to_float(form, "solar_usd_per_mwp", 0.0),
            "bess_USD_per_MWh": to_float(form, "bess_usd_per_mwh", 0.0),
            "bop_USD": to_float(form, "bop_usd", 0.0),
            "depreciation_tenor_years": to_int(form, "depreciation_tenor_years", 20),
        },
        "opex": {
            "solar_om_USD_per_MWp_pa": to_float(form, "solar_om_usd_per_mwp_pa", 6000.0),
            "bess_om_USD_per_MWh_pa": to_float(form, "bess_om_usd_per_mwh_pa", 2000.0),
            "insurance_solar_pct_total_capex": to_float(form, "insurance_solar_pct_capex", 0.0025),
            "insurance_bess_pct_total_capex": to_float(form, "insurance_bess_pct_capex", 0.0025),
            "other_opex_USD_per_MWp_pa": to_float(form, "other_opex_usd_per_mwp_pa", 1000.0),
            "asset_management_USD_per_MWp_pa": to_float(
                form,
                "asset_management_usd_per_mwp_pa",
                3000.0,
            ),
            "land_lease_pct_of_revenue": to_float(form, "land_lease_pct_revenue", 0.005),
            "opex_escalation_cpi_pct_pa": to_float(form, "opex_escalation_pct", 0.04),
        },
        "financial_assumptions": {
            "debt_sizing": {
                "maximum_leverage_pct": to_float(form, "maximum_leverage_pct", 0.7),
                "maximum_debt_tenor_years": to_int(form, "tenor_years", 15),
                "target_dscr_x": to_float(form, "target_dscr", 1.3),
            },
            "interest_rate": {
                "base_rate_floating": to_float(form, "base_rate", 0.06),
                "debt_margin_pct": to_float(form, "debt_margin", 0.0),
            },
            "tax": {
                "corporate_tax_rate_pct": to_float(form, "tax_rate", 0.2),
                "tax_holiday_years": to_int(form, "tax_holiday_years", 5),
                "first_discount_year": to_int(form, "first_discount_year", 13),
                "first_discount_rate": to_float(form, "first_discount_rate", 0.13),
                "second_discount_year": to_int(form, "second_discount_year", 15),
                "second_discount_rate": to_float(form, "second_discount_rate", 0.15),
            },
            "return_expectations": {
                "target_minimum_equity_irr_pct": to_float(
                    form,
                    "target_minimum_equity_irr_pct",
                    0.1,
                )
            },
        },
        "degradation_and_loss": {
            "annual_table": annual_table,
        },
        "retail_tariff_matrix": {
            "mra_buildup_assumption": [
                {"year": 0, "pct": to_float(form, "mra_buildup_year0_pct", 0.1)},
                {"year": 1, "pct": to_float(form, "mra_buildup_year1_pct", 0.3)},
                {"year": 2, "pct": to_float(form, "mra_buildup_year2_pct", 0.3)},
                {"year": 3, "pct": to_float(form, "mra_buildup_year3_pct", 0.3)},
            ]
        },
    }
