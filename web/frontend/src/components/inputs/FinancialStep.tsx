import type { ChangeEvent } from "react";

import type { FieldErrors } from "./formValidation";
import type { ProjectFormValues } from "./formTypes";

interface FinancialStepProps {
  values: ProjectFormValues;
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  errors: FieldErrors;
}

function fieldClassName(error?: string): string {
  return error ? "input-control input-control-error" : "input-control";
}

export function FinancialStep({ values, onChange, errors }: FinancialStepProps): JSX.Element {
  const bessEnabled = values.bess_enabled === "true";

  return (
    <div className="form-grid">
      <label>
        USD/VND exchange rate
        <input
          className={fieldClassName(errors.exchange_rate_usd_vnd)}
          name="exchange_rate_usd_vnd"
          type="number"
          value={values.exchange_rate_usd_vnd}
          onChange={onChange}
        />
        {errors.exchange_rate_usd_vnd ? <span className="field-error">{errors.exchange_rate_usd_vnd}</span> : null}
      </label>
      <label>
        Solar CAPEX (USD/MWp)
        <input
          className={fieldClassName(errors.solar_usd_per_mwp)}
          name="solar_usd_per_mwp"
          type="number"
          value={values.solar_usd_per_mwp}
          onChange={onChange}
        />
        {errors.solar_usd_per_mwp ? <span className="field-error">{errors.solar_usd_per_mwp}</span> : null}
      </label>
      <label className={!bessEnabled ? "field-disabled" : undefined}>
        BESS CAPEX (USD/MWh)
        <input
          className={fieldClassName(errors.bess_usd_per_mwh)}
          name="bess_usd_per_mwh"
          type="number"
          value={values.bess_usd_per_mwh}
          onChange={onChange}
          disabled={!bessEnabled}
        />
        {errors.bess_usd_per_mwh ? <span className="field-error">{errors.bess_usd_per_mwh}</span> : null}
      </label>
      <label>
        Base interest rate
        <input
          className={fieldClassName(errors.base_rate)}
          name="base_rate"
          type="number"
          step="0.0001"
          value={values.base_rate}
          onChange={onChange}
        />
        {errors.base_rate ? <span className="field-error">{errors.base_rate}</span> : null}
      </label>
      <label>
        Debt margin
        <input
          className={fieldClassName(errors.debt_margin)}
          name="debt_margin"
          type="number"
          step="0.0001"
          value={values.debt_margin}
          onChange={onChange}
        />
        {errors.debt_margin ? <span className="field-error">{errors.debt_margin}</span> : null}
      </label>
      <label>
        Debt tenor (years)
        <input className={fieldClassName(errors.tenor_years)} name="tenor_years" type="number" value={values.tenor_years} onChange={onChange} />
        {errors.tenor_years ? <span className="field-error">{errors.tenor_years}</span> : null}
      </label>
      <label>
        Target DSCR
        <input
          className={fieldClassName(errors.target_dscr)}
          name="target_dscr"
          type="number"
          step="0.01"
          value={values.target_dscr}
          onChange={onChange}
        />
        {errors.target_dscr ? <span className="field-error">{errors.target_dscr}</span> : null}
      </label>
      <label>
        Project years
        <input className={fieldClassName(errors.project_years)} name="project_years" type="number" value={values.project_years} onChange={onChange} />
        {errors.project_years ? <span className="field-error">{errors.project_years}</span> : null}
      </label>
      <label>
        Financial close serial
        <input
          className={fieldClassName(errors.financial_close_serial)}
          name="financial_close_serial"
          type="number"
          value={values.financial_close_serial}
          onChange={onChange}
        />
        {errors.financial_close_serial ? <span className="field-error">{errors.financial_close_serial}</span> : null}
      </label>
      <label>
        COD serial
        <input className={fieldClassName(errors.cod_excel_serial)} name="cod_excel_serial" type="number" value={values.cod_excel_serial} onChange={onChange} />
        {errors.cod_excel_serial ? <span className="field-error">{errors.cod_excel_serial}</span> : null}
      </label>
    </div>
  );
}
