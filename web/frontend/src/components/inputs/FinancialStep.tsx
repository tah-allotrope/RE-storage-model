import type { ChangeEvent } from "react";

import type { ProjectFormValues } from "./formTypes";

interface FinancialStepProps {
  values: ProjectFormValues;
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
}

export function FinancialStep({ values, onChange }: FinancialStepProps): JSX.Element {
  return (
    <div className="form-grid">
      <label>
        USD/VND exchange rate
        <input
          name="exchange_rate_usd_vnd"
          type="number"
          value={values.exchange_rate_usd_vnd}
          onChange={onChange}
        />
      </label>
      <label>
        Solar CAPEX (USD/MWp)
        <input name="solar_usd_per_mwp" type="number" value={values.solar_usd_per_mwp} onChange={onChange} />
      </label>
      <label>
        BESS CAPEX (USD/MWh)
        <input name="bess_usd_per_mwh" type="number" value={values.bess_usd_per_mwh} onChange={onChange} />
      </label>
      <label>
        Base interest rate
        <input name="base_rate" type="number" step="0.0001" value={values.base_rate} onChange={onChange} />
      </label>
      <label>
        Debt margin
        <input name="debt_margin" type="number" step="0.0001" value={values.debt_margin} onChange={onChange} />
      </label>
      <label>
        Debt tenor (years)
        <input name="tenor_years" type="number" value={values.tenor_years} onChange={onChange} />
      </label>
      <label>
        Target DSCR
        <input name="target_dscr" type="number" step="0.01" value={values.target_dscr} onChange={onChange} />
      </label>
      <label>
        Project years
        <input name="project_years" type="number" value={values.project_years} onChange={onChange} />
      </label>
      <label>
        Financial close serial
        <input
          name="financial_close_serial"
          type="number"
          value={values.financial_close_serial}
          onChange={onChange}
        />
      </label>
      <label>
        COD serial
        <input name="cod_excel_serial" type="number" value={values.cod_excel_serial} onChange={onChange} />
      </label>
    </div>
  );
}
