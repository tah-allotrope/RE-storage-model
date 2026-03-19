import type { ChangeEvent } from "react";

import type { ProjectFormValues } from "./formTypes";

interface DppaStepProps {
  values: ProjectFormValues;
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
}

export function DppaStep({ values, onChange }: DppaStepProps): JSX.Element {
  return (
    <div className="form-grid">
      <label>
        DPPA enabled
        <select name="dppa_enabled" value={values.dppa_enabled} onChange={onChange}>
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      </label>
      <label>
        Strike price (VND/kWh)
        <input name="strike_price_vnd" type="number" value={values.strike_price_vnd} onChange={onChange} />
      </label>
      <label>
        k-factor
        <input name="k_factor" type="number" step="0.0001" value={values.k_factor} onChange={onChange} />
      </label>
      <label>
        Connection voltage (kV)
        <select name="connection_voltage_kv" value={values.connection_voltage_kv} onChange={onChange}>
          <option value="22">22</option>
          <option value="110">110</option>
        </select>
      </label>
      <label>
        Kpp 22kV
        <input name="kpp_22" type="number" step="0.000001" value={values.kpp_22} onChange={onChange} />
      </label>
      <label>
        Kpp 110kV
        <input name="kpp_110" type="number" step="0.000001" value={values.kpp_110} onChange={onChange} />
      </label>
      <label>
        Off-peak tariff (USD/MWh)
        <input name="tariff_off_peak" type="number" step="0.001" value={values.tariff_off_peak} onChange={onChange} />
      </label>
      <label>
        Standard tariff (USD/MWh)
        <input name="tariff_standard" type="number" step="0.001" value={values.tariff_standard} onChange={onChange} />
      </label>
      <label>
        Peak tariff (USD/MWh)
        <input name="tariff_peak" type="number" step="0.001" value={values.tariff_peak} onChange={onChange} />
      </label>
    </div>
  );
}
