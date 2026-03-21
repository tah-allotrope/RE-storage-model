"""
Unit tests for scenarios.sensitivity — enhanced sensitivity analysis engine.

Tests cover:
1.  _compute_test_values: relative step type produces correct 7-point range.
2.  _compute_test_values: absolute step type produces correct 7-point range.
3.  _compute_test_values: unknown variable raises ValueError.
4.  _compute_test_values: even steps raises ValueError.
5.  _compute_test_values: falls back to default_base when key absent.
6.  SensitivityPoint is a NamedTuple with correct fields.
7.  build_sensitivity_dataframe: produces expected columns and row count.
8.  build_sensitivity_dataframe: irr_range is max-min of irr column.
9.  build_sensitivity_dataframe: empty input returns empty DataFrame.
10. SENSITIVITY_VARIABLES contains all 9 standard variables.
11. STANDARD_VARIABLE_NAMES lists all 9 variable keys.
12. run_sensitivity raises ValueError when no data source in base_params.
13. run_sensitivity raises ValueError for invalid variable name.
14. run_sensitivity raises ValueError for even steps.
15. plot_tornado_chart: saves a PNG file without error (mock pipeline).
16. plot_tornado_chart: raises KeyError for unknown metric.
17. plot_tornado_chart: creates parent directories if missing.
18. run_full_sensitivity: calls run_sensitivity for each standard variable.
19. run_full_sensitivity: custom variable_names subset is respected.
20. run_sensitivity_for_values: raises ValueError when no data source.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from re_storage.scenarios.sensitivity import (
    SENSITIVITY_VARIABLES,
    STANDARD_VARIABLE_NAMES,
    SensitivityPoint,
    _compute_test_values,
    build_sensitivity_dataframe,
    plot_tornado_chart,
    run_full_sensitivity,
    run_sensitivity,
    run_sensitivity_for_values,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_kpis(irr: float = 0.10, npv: float = 1_000_000.0, dscr: float = 1.5) -> dict:
    """Return a minimal KPI dict that matches what run_full_model returns."""
    return {
        "project_irr": irr,
        "equity_irr": irr + 0.03,
        "npv_usd": npv,
        "dscr_min": dscr,
        "dscr_avg": dscr + 0.1,
        "year1_dppa_revenue_usd": 500_000.0,
        "year1_grid_savings_usd": 100_000.0,
        "year1_solar_generation_mwh": 60_000.0,
        "debt_amount_usd": 30_000_000.0,
    }


def _make_sensitivity_results(
    n_vars: int = 3,
    n_points: int = 7,
) -> dict[str, list[SensitivityPoint]]:
    """Build synthetic full-sensitivity results for testing."""
    var_names = STANDARD_VARIABLE_NAMES[:n_vars]
    results: dict[str, list[SensitivityPoint]] = {}
    for i, var in enumerate(var_names):
        points = [
            SensitivityPoint(
                param_value=float(k),
                irr=0.10 + i * 0.01 + k * 0.005,
                npv=1_000_000.0 + k * 50_000.0,
                dscr_min=1.5 - k * 0.05,
                equity_irr=0.13 + k * 0.005,
            )
            for k in range(n_points)
        ]
        results[var] = points
    return results


# ---------------------------------------------------------------------------
# 1-5: _compute_test_values
# ---------------------------------------------------------------------------


class TestComputeTestValues:
    """Tests for _compute_test_values helper."""

    def test_relative_7_points_symmetric(self) -> None:
        """Relative step: 7 points centred on base, symmetric."""
        base_params = {"strike_price_vnd": 1800.0}
        values = _compute_test_values("strike_price_vnd", base_params, steps=7)
        assert len(values) == 7
        # Middle point should equal base
        assert values[3] == pytest.approx(1800.0, rel=1e-9)

    def test_relative_outer_range(self) -> None:
        """Relative ±3 steps at 6.67 %/step ≈ ±20 % total."""
        base_params = {"strike_price_vnd": 1800.0}
        values = _compute_test_values("strike_price_vnd", base_params, steps=7)
        cfg = SENSITIVITY_VARIABLES["strike_price_vnd"]
        expected_low = 1800.0 * (1.0 - 3 * cfg.step_size)
        expected_high = 1800.0 * (1.0 + 3 * cfg.step_size)
        assert values[0] == pytest.approx(expected_low, rel=1e-9)
        assert values[-1] == pytest.approx(expected_high, rel=1e-9)

    def test_absolute_7_points_symmetric(self) -> None:
        """Absolute step: 7 points centred on base."""
        base_params = {"interest_rate_pct": 0.065}
        values = _compute_test_values("interest_rate_pct", base_params, steps=7)
        assert len(values) == 7
        assert values[3] == pytest.approx(0.065, rel=1e-9)

    def test_absolute_outer_range(self) -> None:
        """Absolute ±3 steps: full spread is 2 × 200 bps = 400 bps (0.04)."""
        base_params = {"interest_rate_pct": 0.065}
        values = _compute_test_values("interest_rate_pct", base_params, steps=7)
        cfg = SENSITIVITY_VARIABLES["interest_rate_pct"]
        expected_low = 0.065 - 3 * cfg.step_size
        expected_high = 0.065 + 3 * cfg.step_size
        assert values[0] == pytest.approx(expected_low, rel=1e-9)
        assert values[-1] == pytest.approx(expected_high, rel=1e-9)
        # ±200 bps on each side → full spread = 400 bps = 0.04
        # step_size = 200bps / 3 steps; total = 6 × step = 400 bps = 0.04
        assert abs(values[-1] - values[0]) == pytest.approx(4.0 / 100.0, rel=0.01)

    def test_unknown_variable_raises(self) -> None:
        """Requesting an unknown variable should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown sensitivity variable"):
            _compute_test_values("nonexistent_var", {}, steps=7)

    def test_even_steps_raises(self) -> None:
        """Even number of steps must raise ValueError."""
        with pytest.raises(ValueError, match="odd"):
            _compute_test_values("strike_price_vnd", {}, steps=6)

    def test_fallback_to_default_base(self) -> None:
        """If param key absent from base_params, use default_base."""
        cfg = SENSITIVITY_VARIABLES["strike_price_vnd"]
        values = _compute_test_values("strike_price_vnd", {}, steps=7)
        # Centre should equal default_base
        assert values[3] == pytest.approx(cfg.default_base, rel=1e-9)

    def test_three_step_sweep(self) -> None:
        """steps=3 returns exactly 3 values."""
        values = _compute_test_values("strike_price_vnd", {}, steps=3)
        assert len(values) == 3


# ---------------------------------------------------------------------------
# 6: SensitivityPoint
# ---------------------------------------------------------------------------


class TestSensitivityPoint:
    """Tests for SensitivityPoint named-tuple."""

    def test_named_tuple_fields(self) -> None:
        """SensitivityPoint must have the five expected fields."""
        pt = SensitivityPoint(
            param_value=1800.0,
            irr=0.10,
            npv=1_000_000.0,
            dscr_min=1.5,
            equity_irr=0.13,
        )
        assert pt.param_value == 1800.0
        assert pt.irr == 0.10
        assert pt.npv == 1_000_000.0
        assert pt.dscr_min == 1.5
        assert pt.equity_irr == 0.13

    def test_indexing_matches_fields(self) -> None:
        """Positional indexing must match field order."""
        pt = SensitivityPoint(1.0, 0.1, 2.0, 1.4, 0.15)
        assert pt[0] == 1.0  # param_value
        assert pt[1] == 0.1  # irr


# ---------------------------------------------------------------------------
# 7-9: build_sensitivity_dataframe
# ---------------------------------------------------------------------------


class TestBuildSensitivityDataframe:
    """Tests for build_sensitivity_dataframe."""

    def test_expected_columns(self) -> None:
        """DataFrame must contain all required output columns."""
        results = _make_sensitivity_results(n_vars=2, n_points=7)
        df = build_sensitivity_dataframe(results)
        required = {
            "variable_name",
            "display_name",
            "param_value",
            "irr",
            "npv_usd",
            "dscr_min",
            "equity_irr",
            "irr_range",
            "npv_range",
            "dscr_min_range",
        }
        assert required.issubset(df.columns)

    def test_row_count(self) -> None:
        """Row count = number of variables × points per variable."""
        results = _make_sensitivity_results(n_vars=3, n_points=7)
        df = build_sensitivity_dataframe(results)
        assert len(df) == 3 * 7

    def test_irr_range_equals_max_minus_min(self) -> None:
        """irr_range for a variable must equal max(irr) – min(irr)."""
        results = _make_sensitivity_results(n_vars=1, n_points=7)
        df = build_sensitivity_dataframe(results)
        var = list(results.keys())[0]
        var_df = df[df["variable_name"] == var]
        expected_range = var_df["irr"].max() - var_df["irr"].min()
        # irr_range is constant for the variable (same value in every row)
        assert float(list(var_df["irr_range"])[0]) == pytest.approx(expected_range)

    def test_empty_input_returns_empty_df(self) -> None:
        """Empty full_results dict returns an empty DataFrame."""
        df = build_sensitivity_dataframe({})
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_display_name_populated(self) -> None:
        """display_name must be populated for known variables."""
        results = _make_sensitivity_results(n_vars=1, n_points=3)
        df = build_sensitivity_dataframe(results)
        assert bool(df["display_name"].notna().all())
        assert bool((df["display_name"] != "").all())

    def test_nan_points_handled_gracefully(self) -> None:
        """NaN KPI values should not prevent DataFrame creation."""
        results = {
            "strike_price_vnd": [
                SensitivityPoint(1500.0, float("nan"), float("nan"), float("nan"), float("nan")),
                SensitivityPoint(1800.0, 0.10, 1_000_000.0, 1.5, 0.13),
            ]
        }
        df = build_sensitivity_dataframe(results)
        assert len(df) == 2
        # irr_range should be nan since only one valid point
        assert math.isnan(float(list(df["irr_range"])[0]))


# ---------------------------------------------------------------------------
# 10-11: Variable registry
# ---------------------------------------------------------------------------


class TestVariableRegistry:
    """Tests for SENSITIVITY_VARIABLES and STANDARD_VARIABLE_NAMES."""

    def test_nine_standard_variables(self) -> None:
        """Must define exactly 9 standard sensitivity variables."""
        assert len(SENSITIVITY_VARIABLES) == 9

    def test_standard_names_match_dict_keys(self) -> None:
        """STANDARD_VARIABLE_NAMES must match SENSITIVITY_VARIABLES keys."""
        assert set(STANDARD_VARIABLE_NAMES) == set(SENSITIVITY_VARIABLES.keys())

    def test_all_configs_have_required_fields(self) -> None:
        """Every variable config must have a non-empty display_name and positive step_size."""
        for name, cfg in SENSITIVITY_VARIABLES.items():
            assert cfg.display_name, f"{name}: display_name is empty"
            assert cfg.step_size > 0, f"{name}: step_size must be positive"
            assert cfg.step_type in {"relative", "absolute"}, f"{name}: bad step_type"
            assert cfg.param_key, f"{name}: param_key is empty"

    def test_expected_variable_names_present(self) -> None:
        """The 9 specific variable names from the task spec must be present."""
        expected = {
            "strike_price_vnd",
            "pv_capex_usd_per_mwp",
            "bess_capex_usd_per_mwh",
            "bess_size_mwh",
            "solar_capacity_mwp",
            "interest_rate_pct",
            "bundled_discount_pct",
            "opex_escalation_pct",
            "fmp_descent_pct",
        }
        assert expected.issubset(set(SENSITIVITY_VARIABLES.keys()))


# ---------------------------------------------------------------------------
# 12-14: run_sensitivity input validation
# ---------------------------------------------------------------------------


class TestRunSensitivityValidation:
    """Tests for run_sensitivity parameter validation (no pipeline calls)."""

    def test_no_data_source_raises(self) -> None:
        """base_params without excel_path or project_dir must raise ValueError."""
        with pytest.raises(ValueError, match="excel_path.*project_dir"):
            run_sensitivity({}, "strike_price_vnd")

    def test_invalid_variable_name_raises(self) -> None:
        """Unknown variable name must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown sensitivity variable"):
            run_sensitivity({"excel_path": "x.xlsx"}, "no_such_var")

    def test_even_steps_raises(self) -> None:
        """Even steps must raise ValueError before any pipeline call."""
        with pytest.raises(ValueError, match="odd"):
            run_sensitivity({"excel_path": "x.xlsx"}, "strike_price_vnd", steps=4)


class TestRunSensitivityExecution:
    """Regression tests for pipeline override propagation."""

    def test_excel_path_passes_overrides_via_base_params(self) -> None:
        """Excel sensitivity runs should pass the swept value through base_params."""
        captured_overrides: list[dict[str, Any]] = []

        def _fake_run_full_model(
            path: Path,
            ppa_option: int = 3,
            base_params: dict[str, Any] | None = None,
        ) -> dict[str, float]:
            del path, ppa_option
            params = dict(base_params or {})
            captured_overrides.append(params)
            strike_price_vnd = float(params["strike_price_vnd"])
            return _fake_kpis(irr=strike_price_vnd / 10_000.0)

        with patch(
            "re_storage.pipeline.run_full_model",
            side_effect=_fake_run_full_model,
        ):
            results = run_sensitivity(
                {"excel_path": "dummy.xlsx"},
                "strike_price_vnd",
                steps=3,
            )

        assert [pt.param_value for pt in results] == pytest.approx([1680.0, 1800.0, 1920.0])
        assert [pt.irr for pt in results] == pytest.approx([0.168, 0.18, 0.192])
        assert [item["strike_price_vnd"] for item in captured_overrides] == pytest.approx(
            [1680.0, 1800.0, 1920.0]
        )

    def test_project_dir_passes_overrides_via_base_params(self) -> None:
        """JSON sensitivity runs should vary the selected parameter across iterations."""
        captured_overrides: list[dict[str, Any]] = []

        def _fake_run_model_from_json(
            project_dir: Path,
            ppa_option: int = 3,
            base_params: dict[str, Any] | None = None,
        ) -> dict[str, float]:
            del project_dir, ppa_option
            params = dict(base_params or {})
            captured_overrides.append(params)
            discount_pct = float(params["bundled_discount_pct"])
            return _fake_kpis(irr=discount_pct)

        with patch(
            "re_storage.pipeline.run_model_from_json",
            side_effect=_fake_run_model_from_json,
        ):
            results = run_sensitivity(
                {"project_dir": "dummy-project"},
                "bundled_discount_pct",
                steps=3,
            )

        assert [pt.param_value for pt in results] == pytest.approx(
            [0.1333333333, 0.15, 0.1666666667]
        )
        assert [pt.irr for pt in results] == pytest.approx([0.1333333333, 0.15, 0.1666666667])
        assert [item["bundled_discount_pct"] for item in captured_overrides] == pytest.approx(
            [0.1333333333, 0.15, 0.1666666667]
        )


# ---------------------------------------------------------------------------
# 15-17: plot_tornado_chart
# ---------------------------------------------------------------------------


class TestPlotTornadoChart:
    """Tests for plot_tornado_chart."""

    def _sample_df(self) -> pd.DataFrame:
        return build_sensitivity_dataframe(_make_sensitivity_results(n_vars=4, n_points=7))

    def test_saves_png(self, tmp_path: Path) -> None:
        """plot_tornado_chart must create a PNG file at the specified path."""
        df = self._sample_df()
        out = tmp_path / "tornado.png"
        result_path = plot_tornado_chart(df, out)
        assert result_path == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Missing parent directories should be created automatically."""
        df = self._sample_df()
        out = tmp_path / "nested" / "dir" / "tornado.png"
        plot_tornado_chart(df, out)
        assert out.exists()

    def test_unknown_metric_raises(self, tmp_path: Path) -> None:
        """Requesting a column that doesn't exist must raise KeyError."""
        df = self._sample_df()
        with pytest.raises(KeyError):
            plot_tornado_chart(df, tmp_path / "t.png", metric="nonexistent_col")

    def test_npv_metric(self, tmp_path: Path) -> None:
        """npv_usd metric should render without error."""
        df = self._sample_df()
        out = tmp_path / "npv_tornado.png"
        plot_tornado_chart(df, out, metric="npv_usd")
        assert out.exists()

    def test_returns_path_object(self, tmp_path: Path) -> None:
        """Return value must be a Path instance."""
        df = self._sample_df()
        result = plot_tornado_chart(df, tmp_path / "t.png")
        assert isinstance(result, Path)

    def test_irr_range_metric_uses_precomputed_range_values(self, tmp_path: Path) -> None:
        """Range metrics should render non-zero bar widths from the precomputed columns."""
        df = self._sample_df()
        fig = MagicMock()
        ax = MagicMock()

        with patch("matplotlib.pyplot.subplots", return_value=(fig, ax)):
            result = plot_tornado_chart(df, tmp_path / "t.png", metric="irr_range")

        widths = [float(call.args[1]) for call in ax.barh.call_args_list]
        assert result == tmp_path / "t.png"
        assert widths
        assert any(width < 0 for width in widths)
        assert any(width > 0 for width in widths)
        assert all(width != 0 for width in widths)


# ---------------------------------------------------------------------------
# 18-19: run_full_sensitivity
# ---------------------------------------------------------------------------


class TestRunFullSensitivity:
    """Tests for run_full_sensitivity (pipeline calls are mocked)."""

    def _patched_run_sensitivity(self, return_points: list[SensitivityPoint]):
        """Return a mock that replaces run_sensitivity inside run_full_sensitivity."""
        return MagicMock(return_value=return_points)

    def test_calls_run_sensitivity_for_all_standard_vars(self) -> None:
        """run_full_sensitivity must sweep every standard variable once."""
        dummy_points = [SensitivityPoint(float(i), 0.1, 1e6, 1.5, 0.13) for i in range(7)]
        call_log: list[str] = []

        def _fake_run_sensitivity(base_params, variable_name, steps=7):
            call_log.append(variable_name)
            return dummy_points

        with patch(
            "re_storage.scenarios.sensitivity.run_sensitivity",
            side_effect=_fake_run_sensitivity,
        ):
            results = run_full_sensitivity(
                {"excel_path": "dummy.xlsx"},
                steps=7,
            )

        assert set(call_log) == set(STANDARD_VARIABLE_NAMES)
        assert len(results) == len(STANDARD_VARIABLE_NAMES)

    def test_custom_variable_subset(self) -> None:
        """Passing variable_names restricts the sweep to that subset."""
        subset = ["strike_price_vnd", "pv_capex_usd_per_mwp"]
        call_log: list[str] = []

        def _fake_run_sensitivity(base_params, variable_name, steps=7):
            call_log.append(variable_name)
            return []

        with patch(
            "re_storage.scenarios.sensitivity.run_sensitivity",
            side_effect=_fake_run_sensitivity,
        ):
            run_full_sensitivity(
                {"excel_path": "dummy.xlsx"},
                variable_names=subset,
            )

        assert call_log == subset

    def test_result_keys_match_variable_names(self) -> None:
        """Result dict keys must match the requested variable names."""
        subset = ["strike_price_vnd", "bess_capex_usd_per_mwh"]

        with patch(
            "re_storage.scenarios.sensitivity.run_sensitivity",
            return_value=[],
        ):
            results = run_full_sensitivity(
                {"excel_path": "dummy.xlsx"},
                variable_names=subset,
            )

        assert set(results.keys()) == set(subset)


# ---------------------------------------------------------------------------
# 20: run_sensitivity_for_values (backward compat)
# ---------------------------------------------------------------------------


class TestRunSensitivityForValues:
    """Tests for the backward-compatible run_sensitivity_for_values."""

    def test_no_data_source_raises(self) -> None:
        """Must raise ValueError when neither path argument is provided."""
        with pytest.raises(ValueError, match="project_dir.*excel_path"):
            run_sensitivity_for_values("strike_price_vnd", [1600.0, 1800.0, 2000.0])

    def test_uses_sensitivity_variables_param_key(self) -> None:
        """param_key from SENSITIVITY_VARIABLES should be used for the override."""
        cfg = SENSITIVITY_VARIABLES["bess_size_mwh"]
        captured_params: list[dict] = []

        def _fake_run_full_model(path, ppa_option, base_params=None):
            del path, ppa_option
            captured_params.append(dict(base_params or {}))
            return _fake_kpis()

        with patch(
            "re_storage.pipeline.run_full_model",
            side_effect=_fake_run_full_model,
        ):
            run_sensitivity_for_values(
                "bess_size_mwh",
                [60.0, 66.0],
                excel_path=Path("dummy.xlsx"),
            )

        assert cfg.param_key in captured_params[0]

    def test_project_dir_passes_swept_values_into_json_pipeline(self) -> None:
        """Backward-compatible JSON sweeps should pass per-run overrides into the pipeline."""
        captured_params: list[dict[str, Any]] = []

        def _fake_run_model_from_json(path, ppa_option, base_params=None):
            del path, ppa_option
            params = dict(base_params or {})
            captured_params.append(params)
            value = float(params["bundled_discount_pct"])
            return _fake_kpis(irr=value)

        with patch(
            "re_storage.pipeline.run_model_from_json",
            side_effect=_fake_run_model_from_json,
        ):
            results = run_sensitivity_for_values(
                "bundled_discount_pct",
                [0.13, 0.15],
                project_dir=Path("dummy-project"),
            )

        assert [item["bundled_discount_pct"] for item in captured_params] == pytest.approx(
            [0.13, 0.15]
        )
        assert results[0.13]["project_irr"] == pytest.approx(0.13)
        assert results[0.15]["project_irr"] == pytest.approx(0.15)

    def test_errors_stored_as_dict_with_error_key(self) -> None:
        """If a run raises, result should have 'error' key, not propagate."""
        with patch(
            "re_storage.pipeline.run_full_model",
            side_effect=RuntimeError("boom"),
        ):
            results = run_sensitivity_for_values(
                "strike_price_vnd",
                [1800.0],
                excel_path=Path("dummy.xlsx"),
            )
        assert "error" in results[1800.0]
