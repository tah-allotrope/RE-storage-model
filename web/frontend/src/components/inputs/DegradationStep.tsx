import type { ChangeEvent } from "react";

import type { FieldErrors } from "./formValidation";
import type { ProjectFormValues } from "./formTypes";

interface DegradationStepProps {
  values: ProjectFormValues;
  onChange: (event: ChangeEvent<HTMLTextAreaElement>) => void;
  errors: FieldErrors;
}

export function DegradationStep({ values, onChange, errors }: DegradationStepProps): JSX.Element {
  return (
    <div className="form-grid-single">
      <label>
        Degradation table JSON
        <textarea
          className={errors.degradation_json ? "input-control input-control-error" : "input-control"}
          name="degradation_json"
          rows={12}
          value={values.degradation_json}
          onChange={onChange}
        />
        {errors.degradation_json ? <span className="field-error">{errors.degradation_json}</span> : null}
      </label>
      <p className="form-note">
        Provide an array with {`{ year, pv_retention, battery_retention, battery_with_replacement }`}.
      </p>
    </div>
  );
}
