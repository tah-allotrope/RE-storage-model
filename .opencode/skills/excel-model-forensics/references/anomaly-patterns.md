# Anomaly Patterns

Battery lifetime jumps:

- Symptom: abrupt increase at replacement years (for example Y10->Y11, Y21->Y22).
- Check: replacement-factor column usage in lifetime formulas.

Toggle-gated zero outputs:

- Symptom: whole revenue path becomes zero unexpectedly.
- Check: activation flags in DPPA or equivalent sidecar formulas.

Controlled circular debt sizing:

- Symptom: stale debt results if iterative process/macros not run.
- Check: goal-seek cells and dependency loop outputs.

Balance check column not enforced:

- Symptom: non-zero physics imbalance without blocking behavior.
- Check: whether balance columns are only informational or validated.
