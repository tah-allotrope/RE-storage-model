import type { ChangeEvent } from "react";

import type { ProjectFormValues } from "./formTypes";

interface DegradationStepProps {
  values: ProjectFormValues;
  onChange: (event: ChangeEvent<HTMLTextAreaElement>) => void;
}

export function DegradationStep({ values, onChange }: DegradationStepProps): JSX.Element {
  return (
    <div className="form-grid-single">
      <label>
        Degradation table JSON
        <textarea
          name="degradation_json"
          rows={12}
          value={values.degradation_json}
          onChange={onChange}
        />
      </label>
      <p className="form-note">
        Provide an array with {`{ year, pv_retention, battery_retention, battery_with_replacement }`}.
      </p>
    </div>
  );
}
