import type { ChangeEvent } from "react";

import type { FieldErrors } from "./formValidation";
import type { ProjectFormValues } from "./formTypes";

interface SystemStepProps {
  values: ProjectFormValues;
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  errors: FieldErrors;
}

function fieldClassName(error?: string): string {
  return error ? "input-control input-control-error" : "input-control";
}

export function SystemStep({ values, onChange, errors }: SystemStepProps): JSX.Element {
  const bessEnabled = values.bess_enabled === "true";

  return (
    <div className="form-grid">
      <label>
        Project name
        <input className={fieldClassName(errors.project_name)} name="project_name" value={values.project_name} onChange={onChange} />
      </label>
      <label>
        Installed capacity (kWp)
        <input
          className={fieldClassName(errors.actual_capacity_kwp)}
          name="actual_capacity_kwp"
          type="number"
          value={values.actual_capacity_kwp}
          onChange={onChange}
        />
        {errors.actual_capacity_kwp ? <span className="field-error">{errors.actual_capacity_kwp}</span> : null}
      </label>
      <label>
        Simulation capacity (kWp)
        <input
          className={fieldClassName(errors.simulation_capacity_kwp)}
          name="simulation_capacity_kwp"
          type="number"
          value={values.simulation_capacity_kwp}
          onChange={onChange}
        />
        {errors.simulation_capacity_kwp ? <span className="field-error">{errors.simulation_capacity_kwp}</span> : null}
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Total BESS storage (kWh)
        <input
          className={fieldClassName(errors.total_bess_kwh)}
          name="total_bess_kwh"
          type="number"
          value={values.total_bess_kwh}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.total_bess_kwh ? <span className="field-error">{errors.total_bess_kwh}</span> : null}
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        BESS power rating (kW)
        <input
          className={fieldClassName(errors.bess_power_rating_kw)}
          name="bess_power_rating_kw"
          type="number"
          value={values.bess_power_rating_kw}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.bess_power_rating_kw ? <span className="field-error">{errors.bess_power_rating_kw}</span> : null}
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Depth of discharge
        <input
          className={fieldClassName(errors.dod)}
          name="dod"
          type="number"
          step="0.01"
          value={values.dod}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.dod ? <span className="field-error">{errors.dod}</span> : null}
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Half-cycle efficiency
        <input
          className={fieldClassName(errors.half_cycle_efficiency)}
          name="half_cycle_efficiency"
          type="number"
          step="0.01"
          value={values.half_cycle_efficiency}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.half_cycle_efficiency ? <span className="field-error">{errors.half_cycle_efficiency}</span> : null}
      </label>
      <label>
        BESS enabled
        <select className={fieldClassName(errors.bess_enabled)} name="bess_enabled" value={values.bess_enabled} onChange={onChange}>
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Strategy mode
        <select
          className={fieldClassName(errors.strategy_mode)}
          name="strategy_mode"
          value={values.strategy_mode}
          onChange={onChange}
          disabled={!bessEnabled}
        >
          <option value="1">Arbitrage</option>
          <option value="2">Peak Shaving</option>
        </select>
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Charging mode
        <select
          className={fieldClassName(errors.charging_mode)}
          name="charging_mode"
          value={values.charging_mode}
          onChange={onChange}
          disabled={!bessEnabled}
        >
          <option value="1">Time Window</option>
          <option value="2">Pre-charge</option>
        </select>
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Charge start hour
        <input
          className={fieldClassName(errors.charge_start_hour)}
          name="charge_start_hour"
          type="number"
          value={values.charge_start_hour}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.charge_start_hour ? <span className="field-error">{errors.charge_start_hour}</span> : null}
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Charge end hour
        <input
          className={fieldClassName(errors.charge_end_hour)}
          name="charge_end_hour"
          type="number"
          value={values.charge_end_hour}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.charge_end_hour ? <span className="field-error">{errors.charge_end_hour}</span> : null}
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Min PV direct-to-load share
        <input
          className={fieldClassName(errors.min_direct_pv_share)}
          name="min_direct_pv_share"
          type="number"
          step="0.01"
          value={values.min_direct_pv_share}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.min_direct_pv_share ? <span className="field-error">{errors.min_direct_pv_share}</span> : null}
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Active PV-to-BESS share
        <input
          className={fieldClassName(errors.active_pv2bess_share)}
          name="active_pv2bess_share"
          type="number"
          step="0.01"
          value={values.active_pv2bess_share}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.active_pv2bess_share ? <span className="field-error">{errors.active_pv2bess_share}</span> : null}
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Precharge target SoC (kWh)
        <input
          className={fieldClassName(errors.precharge_target_soc_kwh)}
          name="precharge_target_soc_kwh"
          type="number"
          value={values.precharge_target_soc_kwh}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.precharge_target_soc_kwh ? <span className="field-error">{errors.precharge_target_soc_kwh}</span> : null}
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        Precharge target hour
        <input
          className={fieldClassName(errors.precharge_target_hour)}
          name="precharge_target_hour"
          type="number"
          value={values.precharge_target_hour}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.precharge_target_hour ? <span className="field-error">{errors.precharge_target_hour}</span> : null}
      </label>
    </div>
  );
}
