# MVP limitations and acceptance checks

## Known limits

- Synthetic demo traces are not representative of fleet or OEM distributions.
- No customer-specific schema, DTC dictionary, signal calibration, or unit validation exists yet.
- Intent matching is simple phrase logic; it is not an unrestricted chat system.
- The ten-minute timeline is a chosen demo window, not a validated diagnostic interval.
- Energy comparison is a simple mean of available `energy_consumption` samples; it does not normalize route, weather, load, driver, or HVAC effects.
- Correlation is not causal diagnosis. A model can paraphrase evidence incorrectly, so preserve the evidence and use human review.
- No authentication, tenant isolation, encryption-at-rest setup, durable audit history, backup workflow, or production deployment controls.
- The `<2 sec` target, RAM budget, local model quality, and operation on vehicle/edge compute have not been benchmarked.
- A green API health check proves only that the local process is running; it does not prove data correctness or automotive safety.

## Pilot acceptance (proposed; agree with customer)

1. Data owner signs off on a field mapping, provenance, units, and synthetic/de-identified sample.
2. For an agreed set of at least 20 known investigations, every displayed evidence row must match the reference event/time range; missing/invalid records must remain visible.
3. Service technicians compare the current workflow and workbench on the same tasks. Measure time-to-first-relevant-evidence, completion, evidence correctness, and trust; do not claim time savings until measured.
4. No unsupported causal claims or unsafe repair actions appear in the evaluated outputs. Deterministic summaries remain available with model disabled.
5. Validate packaging, local-only network behavior, data deletion, restart/recovery, and performance on the actual pilot laptop.
6. Obtain explicit pilot feedback and a paid continuation decision before investing in broad vehicle coverage.
