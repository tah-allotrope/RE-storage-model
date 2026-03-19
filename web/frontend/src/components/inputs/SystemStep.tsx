import type { ChangeEvent } from "react";

import type { ProjectFormValues } from "./formTypes";

interface SystemStepProps {
  values: ProjectFormValues;
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
}

export function SystemStep({ values, onChange }: SystemStepProps): JSX.Element {
  return (
    <div className="form-grid">
      <label>
        Project name
        <input name="project_name" value={values.project_name} onChange={onChange} />
      </label>
      <label>
        Installed capacity (kWp)
        <input name="actual_capacity_kwp" type="number" value={values.actual_capacity_kwp} onChange={onChange} />
      </label>
      <label>
        Simulation capacity (kWp)
        <input name="simulation_capacity_kwp" type="number" value={values.simulation_capacity_kwp} onChange={onChange} />
      </label>
      <label>
        Total BESS storage (kWh)
        <input name="total_bess_kwh" type="number" value={values.total_bess_kwh} onChange={onChange} />
      </label>
      <label>
        BESS power rating (kW)
        <input name="bess_power_rating_kw" type="number" value={values.bess_power_rating_kw} onChange={onChange} />
      </label>
      <label>
        Depth of discharge
        <input name="dod" type="number" step="0.01" value={values.dod} onChange={onChange} />
      </label>
      <label>
        Half-cycle efficiency
        <input
          name="half_cycle_efficiency"
          type="number"
          step="0.01"
          value={values.half_cycle_efficiency}
          onChange={onChange}
        />
      </label>
      <label>
        BESS enabled
        <select name="bess_enabled" value={values.bess_enabled} onChange={onChange}>
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      </label>
      <label>
        Strategy mode
        <select name="strategy_mode" value={values.strategy_mode} onChange={onChange}>
          <option value="1">Arbitrage</option>
          <option value="2">Peak Shaving</option>
        </select>
      </label>
      <label>
        Charging mode
        <select name="charging_mode" value={values.charging_mode} onChange={onChange}>
          <option value="1">Time Window</option>
          <option value="2">Pre-charge</option>
        </select>
      </label>
      <label>
        Charge start hour
        <input name="charge_start_hour" type="number" value={values.charge_start_hour} onChange={onChange} />
      </label>
      <label>
        Charge end hour
        <input name="charge_end_hour" type="number" value={values.charge_end_hour} onChange={onChange} />
      </label>
      <label>
        Min PV direct-to-load share
        <input
          name="min_direct_pv_share"
          type="number"
          step="0.01"
          value={values.min_direct_pv_share}
          onChange={onChange}
        />
      </label>
      <label>
        Active PV-to-BESS share
        <input
          name="active_pv2bess_share"
          type="number"
          step="0.01"
          value={values.active_pv2bess_share}
          onChange={onChange}
        />
      </label>
      <label>
        Precharge target SoC (kWh)
        <input
          name="precharge_target_soc_kwh"
          type="number"
          value={values.precharge_target_soc_kwh}
          onChange={onChange}
        />
      </label>
      <label>
        Precharge target hour
        <input name="precharge_target_hour" type="number" value={values.precharge_target_hour} onChange={onChange} />
      </label>
    </div>
  );
}
