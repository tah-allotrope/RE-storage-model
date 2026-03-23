import type { ChangeEvent } from "react";

import type { FieldErrors } from "./formValidation";
import type { ProjectFormValues } from "./formTypes";

interface DppaStepProps {
  values: ProjectFormValues;
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  errors: FieldErrors;
}

function fieldClassName(error?: string): string {
  return error ? "input-control input-control-error" : "input-control";
}

export function DppaStep({ values, onChange, errors }: DppaStepProps): JSX.Element {
  const dppaEnabled = values.dppa_enabled === "true";

  return (
    <div className="form-grid">
      <label>
        DPPA enabled
        <select className={fieldClassName(errors.dppa_enabled)} name="dppa_enabled" value={values.dppa_enabled} onChange={onChange}>
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      </label>
      <label className={!dppaEnabled ? "field-disabled" : undefined}>
        Strike price (VND/kWh)
        <input
          className={fieldClassName(errors.strike_price_vnd)}
          name="strike_price_vnd"
          type="number"
          value={values.strike_price_vnd}
          onChange={onChange}
          disabled={!dppaEnabled}
        />
        {errors.strike_price_vnd ? <span className="field-error">{errors.strike_price_vnd}</span> : null}
      </label>
      <label className={!dppaEnabled ? "field-disabled" : undefined}>
        k-factor
        <input
          className={fieldClassName(errors.k_factor)}
          name="k_factor"
          type="number"
          step="0.0001"
          value={values.k_factor}
          onChange={onChange}
          disabled={!dppaEnabled}
        />
        {errors.k_factor ? <span className="field-error">{errors.k_factor}</span> : null}
      </label>
      <label>
        Connection voltage (kV)
        <select
          className={fieldClassName(errors.connection_voltage_kv)}
          name="connection_voltage_kv"
          value={values.connection_voltage_kv}
          onChange={onChange}
        >
          <option value="22">22</option>
          <option value="110">110</option>
        </select>
      </label>
      <label className={!dppaEnabled ? "field-disabled" : undefined}>
        Kpp 22kV
        <input
          className={fieldClassName(errors.kpp_22)}
          name="kpp_22"
          type="number"
          step="0.000001"
          value={values.kpp_22}
          onChange={onChange}
          disabled={!dppaEnabled}
        />
        {errors.kpp_22 ? <span className="field-error">{errors.kpp_22}</span> : null}
      </label>
      <label className={!dppaEnabled ? "field-disabled" : undefined}>
        Kpp 110kV
        <input
          className={fieldClassName(errors.kpp_110)}
          name="kpp_110"
          type="number"
          step="0.000001"
          value={values.kpp_110}
          onChange={onChange}
          disabled={!dppaEnabled}
        />
        {errors.kpp_110 ? <span className="field-error">{errors.kpp_110}</span> : null}
      </label>
      <label>
        Off-peak tariff (USD/MWh)
        <input
          className={fieldClassName(errors.tariff_off_peak)}
          name="tariff_off_peak"
          type="number"
          step="0.001"
          value={values.tariff_off_peak}
          onChange={onChange}
        />
        {errors.tariff_off_peak ? <span className="field-error">{errors.tariff_off_peak}</span> : null}
      </label>
      <label>
        Standard tariff (USD/MWh)
        <input
          className={fieldClassName(errors.tariff_standard)}
          name="tariff_standard"
          type="number"
          step="0.001"
          value={values.tariff_standard}
          onChange={onChange}
        />
        {errors.tariff_standard ? <span className="field-error">{errors.tariff_standard}</span> : null}
      </label>
      <label>
        Peak tariff (USD/MWh)
        <input
          className={fieldClassName(errors.tariff_peak)}
          name="tariff_peak"
          type="number"
          step="0.001"
          value={values.tariff_peak}
          onChange={onChange}
        />
        {errors.tariff_peak ? <span className="field-error">{errors.tariff_peak}</span> : null}
      </label>
    </div>
  );
}
