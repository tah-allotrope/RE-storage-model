"""Unit tests for scenario runner topology support."""

from __future__ import annotations

import pytest

from re_storage.scenarios.runner import run_all_scenarios
from re_storage.scenarios.sensitivity import run_sensitivity_for_values


class TestScenarioRunnerTopology:
    def test_run_all_scenarios_invalid_topology_raises(self):
        """ValueError for bad topology in run_all_scenarios."""
        with pytest.raises(ValueError, match="dppa_topology"):
            run_all_scenarios(
                project_dir="dummy",
                dppa_topology="invalid",
            )

    def test_run_all_scenarios_accepts_offsite(self):
        """run_all_scenarios accepts offsite topology without error at validation stage."""
        # The pipeline will fail on the dummy directory, but the topology
        # parameter should be accepted (validation passes before pipeline run).
        results = run_all_scenarios(
            project_dir="dummy",
            dppa_topology="offsite",
            ppa_options=[1],
        )
        assert 1 in results
        assert "error" in results[1]


class TestSensitivityTopology:
    def test_run_sensitivity_invalid_topology_raises(self):
        """ValueError for bad topology in run_sensitivity_for_values."""
        with pytest.raises(ValueError, match="dppa_topology"):
            run_sensitivity_for_values(
                variable_name="strike_price",
                test_values=[0.05, 0.06],
                project_dir="dummy",
                dppa_topology="invalid",
            )
