# Startup roadmap: from demo to a credible pilot

## Venture thesis

**Customer wedge:** independent or OEM-affiliated service engineering teams investigating intermittent vehicle warnings from exported traces. Avoid broad “AI for all vehicles” positioning until one high-frequency workflow is proven.

**Pain hypothesis:** engineers lose time correlating timestamps across logs, event codes, and signal files; a reusable evidence timeline could shorten investigation and make handoffs clearer. This is a hypothesis to validate with customer interviews, not a proven market fact.

**Buyer/user:** service engineering or aftersales diagnostics leader (buyer); diagnostic engineer/technician (daily user); vehicle-data or cybersecurity owner (approver). Potential early channel: one engineering-services provider or fleet maintenance operator willing to provide a narrowly scoped, de-identified dataset.

**Value proposition:** turn one authorized local dataset into a searchable, evidence-linked incident timeline without cloud upload or a vehicle connection.

## Stage 0 — Validate workflow before building more (1–2 weeks)

- Interview 8–12 service/diagnostic professionals. Ask them to walk through the last real investigation, tools/files used, handoffs, elapsed time, recurring categories, and data access constraints. Do not lead with “Would you use AI?”
- Ask for a redacted sample export and permission path; map who can authorize it and how long approval takes.
- Collect baseline measures: time to gather relevant traces, time to identify candidate evidence, repeat investigations, and current software spend/process.
- Narrow to one trigger (e.g. thermal warning) and one workflow. Continue only if the pain recurs and someone can sponsor a pilot.

**Gate:** at least three interviewees independently describe the same costly workflow; one named design partner is willing to define a sample and pilot success criteria.

## Stage 1 — Software demo (current repo; 1–3 weeks)

- Generate synthetic JSONL traces and run UI/API completely on a laptop.
- Demo fixed questions, evidence, missing-data quality, recurrence, and limitations.
- Test whether a technician can find the reference evidence. Track answer/evidence correctness, not model eloquence.
- Keep no cloud, no hardware dependency, no actuation, and no raw customer data.

**Gate:** scripted scenarios are reproducible, query results match ground truth, and users understand the provenance and caveats.

## Stage 2 — Paid design-partner pilot (4–8 weeks after data approval)

Scope to one team, one export format, one warning family, 20–50 approved investigations, one workstation or controlled laptop image, and a named human reviewer. Write a short pilot agreement covering data rights, security, retention, support, IP, and success metrics. Charge for integration/pilot work if buyer accepts; do not promise production deployment.

Deliverables: adapter and mapping document; baseline workflow measurement; local deployment; evaluated evidence reports; deletion confirmation; pilot review with buyer. Use deterministic parsing/analytics; keep model optional.

**Success measures:** task completion, relevant-evidence precision/recall against agreed references, time-to-evidence versus baseline, rate of “no data / unknown” correctness, usability feedback, and conversion to a paid next phase. Agree numerical thresholds with the partner before the trial.

## Stage 3 — Productize only repeated needs (2–4 months)

- Convert the first integration into a versioned adapter contract and validation tool.
- Add auth, role-based access, tenant boundaries (if multi-user), managed retention/deletion, audit trail, encryption/backup controls, signed releases, installer/updates, and security review before any broader deployment.
- Build a reviewed diagnostic knowledge pack with explicit source citations/versioning if customers ask for repair context; do not let a language model invent a fault tree.
- Benchmark local model/no-model response time, memory, and answer faithfulness on the customer's approved hardware and cases.
- Design support, onboarding, pricing, and integration economics using observed pilot effort.

## Stage 4 — Repeatable go-to-market

Expand only when a second customer has similar data and workflow. Package a repeatable private/on-prem installation, dataset adapter onboarding, and recurring support/license offer. Avoid OEM-wide integration claims until procurement, cybersecurity, and data-access requirements are understood.

## Data collection plan

1. **Discovery:** collect no raw data; capture workflow narratives and publicly shareable schema examples.
2. **Prototype:** use generated data plus documented ground truth. Mark all synthetic rows (`SIM-` IDs, `data_origin=simulated`).
3. **Design partner:** get written authorization first. Start with de-identified, limited-duration traces transferred through a customer-approved channel; record provenance and permitted use; restrict access; set a deletion date; keep the local model only.
4. **Labeling:** ask a qualified engineer to annotate incident start, relevant event codes, expected time windows, data gaps, and acceptable answer wording. Keep reviewer and confidence metadata.
5. **Evaluation:** separate cases by vehicle/program/time to avoid leakage; freeze a held-out set; measure evidence retrieval and unsupported claims. Do not train/fine-tune on customer logs unless explicitly licensed.

## Business model hypotheses to test

- Paid data adapter + pilot services, followed by annual team/workstation license and support.
- Per vehicle program or engineering team subscription for offline deployment.
- Avoid per-query SaaS pricing as the initial fit: the data sensitivity and offline constraint make procurement, integration, and local support central.

These are hypotheses. Price using value and deployment/support cost discovered in pilots; do not publish pricing until buyer conversations support it.

## 90-day founder sequence

| Weeks | Founder focus | Evidence of progress |
|---|---|---|
| 1–2 | Interviews and workflow mapping | Repeated pain, champion, data authorization path |
| 3–4 | Demo hardening and synthetic eval | Reproducible evidence accuracy, usable demo |
| 5–6 | Partner scope, security/data terms | Signed pilot plan and approved sample route |
| 7–10 | One adapter and controlled pilot | Baseline comparison, issue log, user feedback |
| 11–12 | Pilot review and commercial decision | Paid continuation, revised wedge, or stop/pivot |

## Risks to test early

- **Data access dominates:** partner cannot share traces. Mitigate with on-prem trial and a data-processing agreement; stop before building generic adapters.
- **Each OEM format is bespoke:** integration cost overwhelms license revenue. Measure mapping hours and repeatability on the second source.
- **Evidence is incomplete or clocks disagree:** outputs mislead. Surface provenance, quality, unit mapping, timezone, and uncertainty; do not summarize missing values away.
- **AI erodes trust:** keep deterministic numbers, visible evidence, grounded language, optional model off switch, and a clear “unknown” response.
- **Safety/security review blocks rollout:** stay read-only and local; complete security architecture and customer review before production data.
- **No budget owner:** require a named champion, buying path, and paid next step as a continuation gate.
