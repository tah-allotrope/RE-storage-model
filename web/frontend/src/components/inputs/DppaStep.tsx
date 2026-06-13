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
  const ppaOption = values.ppa_option;
  const isBundled = ppaOption === "1";
  const isSeparate = ppaOption === "2";
  const isDppa = ppaOption === "3";
  const isFixedPpa = ppaOption === "4";
  const tariffMode = values.tariff_mode;
  const isTwoComponent = tariffMode === "2-component" || tariffMode === "both";

  return (
    <div className="form-grid">
      <label>
        DPPA enabled
        <select className={fieldClassName(errors.dppa_enabled)} name="dppa_enabled" value={values.dppa_enabled} onChange={onChange}>
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      </label>
      <label>
        PPA option
        <select className={fieldClassName(errors.ppa_option)} name="ppa_option" value={values.ppa_option} onChange={onChange}>
          <option value="1">Option 1 - Bundled discount</option>
          <option value="2">Option 2 - Separate PV + BESS discount</option>
          <option value="3">Option 3 - DPPA / CfD</option>
          <option value="4">Option 4 - Fixed EVN PPA</option>
        </select>
      </label>
      <label className={!isDppa || !dppaEnabled ? "field-disabled" : undefined}>
        Strike price (VND/kWh)
        <input
          className={fieldClassName(errors.strike_price_vnd)}
          name="strike_price_vnd"
          type="number"
          value={values.strike_price_vnd}
          onChange={onChange}
          disabled={!dppaEnabled || !isDppa}
        />
        {errors.strike_price_vnd ? <span className="field-error">{errors.strike_price_vnd}</span> : null}
      </label>
      <label className={!isDppa || !dppaEnabled ? "field-disabled" : undefined}>
        k-factor
        <input
          className={fieldClassName(errors.k_factor)}
          name="k_factor"
          type="number"
          step="0.0001"
          value={values.k_factor}
          onChange={onChange}
          disabled={!dppaEnabled || !isDppa}
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
      <label className={!isDppa || !dppaEnabled ? "field-disabled" : undefined}>
        Kpp 22kV
        <input
          className={fieldClassName(errors.kpp_22)}
          name="kpp_22"
          type="number"
          step="0.000001"
          value={values.kpp_22}
          onChange={onChange}
          disabled={!dppaEnabled || !isDppa}
        />
        {errors.kpp_22 ? <span className="field-error">{errors.kpp_22}</span> : null}
      </label>
      <label className={!isDppa || !dppaEnabled ? "field-disabled" : undefined}>
        Kpp 110kV
        <input
          className={fieldClassName(errors.kpp_110)}
          name="kpp_110"
          type="number"
          step="0.000001"
          value={values.kpp_110}
          onChange={onChange}
          disabled={!dppaEnabled || !isDppa}
        />
        {errors.kpp_110 ? <span className="field-error">{errors.kpp_110}</span> : null}
      </label>
      <label className={!isBundled ? "field-disabled" : undefined}>
        Bundled discount
        <input
          className={fieldClassName(errors.bundled_discount_pct)}
          name="bundled_discount_pct"
          type="number"
          step="0.01"
          value={values.bundled_discount_pct}
          onChange={onChange}
          disabled={!isBundled}
        />
        {errors.bundled_discount_pct ? <span className="field-error">{errors.bundled_discount_pct}</span> : null}
      </label>
      <label>
        Revenue escalation
        <input
          className={fieldClassName(errors.revenue_escalation_pct)}
          name="revenue_escalation_pct"
          type="number"
          step="0.01"
          value={values.revenue_escalation_pct}
          onChange={onChange}
        />
        {errors.revenue_escalation_pct ? <span className="field-error">{errors.revenue_escalation_pct}</span> : null}
      </label>
      <label className={!isSeparate ? "field-disabled" : undefined}>
        PV discount
        <input
          className={fieldClassName(errors.pv_discount_pct)}
          name="pv_discount_pct"
          type="number"
          step="0.01"
          value={values.pv_discount_pct}
          onChange={onChange}
          disabled={!isSeparate}
        />
        {errors.pv_discount_pct ? <span className="field-error">{errors.pv_discount_pct}</span> : null}
      </label>
      <label className={!isSeparate ? "field-disabled" : undefined}>
        BESS discount
        <input
          className={fieldClassName(errors.bess_discount_pct)}
          name="bess_discount_pct"
          type="number"
          step="0.01"
          value={values.bess_discount_pct}
          onChange={onChange}
          disabled={!isSeparate}
        />
        {errors.bess_discount_pct ? <span className="field-error">{errors.bess_discount_pct}</span> : null}
      </label>
      <label className={!isFixedPpa ? "field-disabled" : undefined}>
        Fixed PPA price (USD/MWh)
        <input
          className={fieldClassName(errors.fixed_ppa_price_usd_per_mwh)}
          name="fixed_ppa_price_usd_per_mwh"
          type="number"
          step="0.01"
          value={values.fixed_ppa_price_usd_per_mwh}
          onChange={onChange}
          disabled={!isFixedPpa}
        />
        {errors.fixed_ppa_price_usd_per_mwh ? <span className="field-error">{errors.fixed_ppa_price_usd_per_mwh}</span> : null}
      </label>
      <label className={!isFixedPpa ? "field-disabled" : undefined}>
        Fixed PPA curtailment
        <input
          className={fieldClassName(errors.fixed_ppa_curtailment_pct)}
          name="fixed_ppa_curtailment_pct"
          type="number"
          step="0.01"
          value={values.fixed_ppa_curtailment_pct}
          onChange={onChange}
          disabled={!isFixedPpa}
        />
        {errors.fixed_ppa_curtailment_pct ? <span className="field-error">{errors.fixed_ppa_curtailment_pct}</span> : null}
      </label>
      <label className={!isFixedPpa ? "field-disabled" : undefined}>
        Fixed PPA transmission loss
        <input
          className={fieldClassName(errors.fixed_ppa_tx_loss_pct)}
          name="fixed_ppa_tx_loss_pct"
          type="number"
          step="0.01"
          value={values.fixed_ppa_tx_loss_pct}
          onChange={onChange}
          disabled={!isFixedPpa}
        />
        {errors.fixed_ppa_tx_loss_pct ? <span className="field-error">{errors.fixed_ppa_tx_loss_pct}</span> : null}
      </label>
      <label className={!isDppa ? "field-disabled" : undefined}>
        Market price descent
        <input
          className={fieldClassName(errors.fmp_descent_pct)}
          name="fmp_descent_pct"
          type="number"
          step="0.01"
          value={values.fmp_descent_pct}
          onChange={onChange}
          disabled={!isDppa}
        />
        {errors.fmp_descent_pct ? <span className="field-error">{errors.fmp_descent_pct}</span> : null}
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
      <label>
        Tariff mode
        <select
          className={fieldClassName(errors.tariff_mode)}
          name="tariff_mode"
          value={values.tariff_mode}
          onChange={onChange}
        >
          <option value="1-component">1-component (energy only)</option>
          <option value="2-component">2-component (Ca energy + Cp demand)</option>
          <option value="both">Compare both modes</option>
        </select>
        {errors.tariff_mode ? <span className="field-error">{errors.tariff_mode}</span> : null}
      </label>
      <label className={!isTwoComponent ? "field-disabled" : undefined}>
        Cp demand charge (VND/kW/month)
        <input
          className={fieldClassName(errors.cp_demand_vnd_per_kw)}
          name="cp_demand_vnd_per_kw"
          type="number"
          step="1"
          value={values.cp_demand_vnd_per_kw}
          onChange={onChange}
          disabled={!isTwoComponent}
        />
        {errors.cp_demand_vnd_per_kw ? (
          <span className="field-error">{errors.cp_demand_vnd_per_kw}</span>
        ) : null}
      </label>
      <label className={!isTwoComponent ? "field-disabled" : undefined}>
        Ca off-peak rate (VND/kWh)
        <input
          className={fieldClassName(errors.evn_tariff_off_peak_vnd)}
          name="evn_tariff_off_peak_vnd"
          type="number"
          step="1"
          value={values.evn_tariff_off_peak_vnd}
          onChange={onChange}
          disabled={!isTwoComponent}
        />
        {errors.evn_tariff_off_peak_vnd ? (
          <span className="field-error">{errors.evn_tariff_off_peak_vnd}</span>
        ) : null}
      </label>
      <label className={!isTwoComponent ? "field-disabled" : undefined}>
        Ca standard rate (VND/kWh)
        <input
          className={fieldClassName(errors.evn_tariff_standard_vnd)}
          name="evn_tariff_standard_vnd"
          type="number"
          step="1"
          value={values.evn_tariff_standard_vnd}
          onChange={onChange}
          disabled={!isTwoComponent}
        />
        {errors.evn_tariff_standard_vnd ? (
          <span className="field-error">{errors.evn_tariff_standard_vnd}</span>
        ) : null}
      </label>
      <label className={!isTwoComponent ? "field-disabled" : undefined}>
        Ca peak rate (VND/kWh)
        <input
          className={fieldClassName(errors.evn_tariff_peak_vnd)}
          name="evn_tariff_peak_vnd"
          type="number"
          step="1"
          value={values.evn_tariff_peak_vnd}
          onChange={onChange}
          disabled={!isTwoComponent}
        />
        {errors.evn_tariff_peak_vnd ? (
          <span className="field-error">{errors.evn_tariff_peak_vnd}</span>
        ) : null}
      </label>
    </div>
  );
}
