---
_assemble: assemble-generate
_of_phase: generate
_reads:
  - architecture diagram (built inline via agent-advisor-build-diagram.md)
  - recommendation doc + mini-brief (filled inline in agent-advisor-generate.md)
  - HTML report (agent-advisor-generate-report.md contribution)
_produces:
  - diagram.md
  - recommendation.md
  - mini-brief.md
---

# Generate — Assemble the recommendation deliverables

> **Assembler unit.** The Generate phase builds the architecture diagram
> (`diagram.md`), fills the 12-section recommendation document
> (`recommendation.md`), and writes the `mini-brief.md` inline within
> `agent-advisor-generate.md` (Steps 2–4.5); the `generate-report` fragment then renders the
> HTML report. This unit records the artifact-level contract for the phase: it is
> the single creator of `diagram.md`, `recommendation.md`, and `mini-brief.md`,
> and its postconditions (declared on the phase) are the phase's completion gate.
> See `agent-advisor-generate.md` § Steps 2–5 for the section fill order, the freshness footer,
> and the Step 5.5 recommendation-review sidebar that must precede any gate.
