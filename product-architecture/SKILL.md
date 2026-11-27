---
name: product-architecture
description: >-
  Create an upfront, founder-readable architecture plan for a new product, or review the
  architecture impact of a consequential feature or project checkpoint. Covers infrastructure,
  code quality, security and data, observability and cost, and failure and rollback. Use before
  implementation begins, or when a change could alter system boundaries, data ownership,
  integrations, deployment, risk, or operating costs.
---

# product-architecture

Turn product scope and real constraints into a coherent, appropriately flexible architecture
before implementation. Review it again when consequential changes could invalidate its
assumptions. This is a **planning skill**, not a launch audit or a living specification of
shipped behavior. It recommends a concrete, stage-appropriate technology stack and gets the
user's approval before treating that stack as selected.

The architecture plan records the approved intended system, consequential decisions, and a
concise dated implementation status; it changes when material decisions or their status change.
Detailed current behavior belongs in the living `specs/engineering/` documents maintained by
`product-engineering`. `product-launch-audit` separately assesses the running product's launch
readiness. An approved plan alone does not establish what has shipped or whether it is safe to
launch.

## When to Use

- **New product:** after product scope is clear enough to describe its core journeys and before
  the first implementation plan or code.
- **Architecture checkpoint:** before a new or changed decision that adds or changes a system
  boundary, data ownership or sensitivity, authentication, an external service, AI processing,
  deployment, reliability expectations, or a material cost driver.
- **Existing product without an architecture map:** establish a baseline from the shipped
  system before planning a cross-cutting change.

Do not run for every unit or routine localized feature. `product-launch-audit` evaluates whether
an existing app is ready to go live; this skill decides how the system should fit together and
how it should evolve.

Keep the plan concise enough to read as a shared project-wide reference. A target architecture
is the simplest coherent design for the confirmed stage and known product scope, not a forecast
of scale-stage infrastructure. Include a later component when it serves a concrete planned
requirement, not merely because the product might grow. Distinguish an approved future choice
from an option to evaluate later; do not make a deferred component an implicit default.

## Product stages

- **Finding Product-Market-Fit (PMF):** Testing whether a specific group finds enough value to
  return, pay, or change its behavior, including pilots and early products searching for fit.
  Prioritize learning quickly while protecting users and their data.
- **Growth:** There is meaningful evidence that the product works for a group of users; the
  focus is acquiring and serving more of them reliably. Make delivery, support, and operations
  repeatable.
- **Scale:** Usage is substantial or demanding, and failures or inefficiencies have broader
  impact. Multiple teams, complex operations, or stricter customer expectations may also drive
  this stage. Manage reliability, security, cost, and coordination across a larger system.

These are not strict user-count or revenue thresholds. Assess actual risks independently: a
small product handling highly sensitive data may need stronger controls immediately, while a
popular but simple product may not need elaborate infrastructure.

## Inputs and Boundaries

- Read the product spec and flows, if present. For new products with unclear user outcomes,
  scope, or priorities, recommend the user run `/product-scoping` first and stop; do not invoke
  it automatically. A sufficiently clear scope does not require that skill or its files.
- Inspect the relevant code and `specs/engineering/` for an existing product. Check dependency
  manifests and lockfiles, runtime/framework configuration, deployment files, database and
  authentication setup, and existing engineering documentation. Report the verified current
  stack separately from the proposed stack; name the evidence and clearly say when a layer is
  absent or cannot be verified. Do not infer an existing stack from skills, examples, or
  documentation that does not describe the shipped application.
- Use an already confirmed product stage when available; otherwise briefly explain Finding
  Product-Market-Fit (PMF), Growth, and Scale using the definitions above, then ask the user to
  confirm one. Do not silently apply scale assumptions to an early product or defer controls
  needed for its actual risks.
- Treat provider choices, capacity estimates, and user-provided constraints as facts only when
  supported. Mark estimates and assumptions, and surface material unknowns instead of guessing.
- When a budget is discussed or estimated, express it in USD unless the user explicitly names a
  different currency. Do not ask the user which currency to use.
- Keep the plan understandable to a non-technical founder: explain technical terms briefly and
  frame tradeoffs as user impact, risk, cost, and reversibility.
- Do not write application code, implement infrastructure, or claim a design is secure or
  production-ready just because it is documented.

## Workflow

### 1. Establish the planning boundary

Summarize the product or change, its stage, the critical user journeys, known constraints, and
what is intentionally out of scope. For a checkpoint, identify the affected parts of the
existing architecture and distinguish unchanged areas from proposed changes.

If a missing answer could materially change the system shape or a hard-to-reverse decision,
ask a focused question before finalizing. Otherwise record it as an assumption or an open
question with a recommended default.

### 2. Draw the system shape

Create one concise system-context diagram and explain it in plain language. Show only
meaningful elements:

- users and other actors;
- application components and their responsibilities;
- data stores and the data each owns;
- external services and what crosses each boundary;
- trust boundaries and important synchronous or asynchronous flows.

Name boundaries and responsibilities before recommending products or frameworks. Then propose
a concrete stack sized to the confirmed product stage, existing codebase, and constraints.
For each stack layer, give a recommended option, a credible alternative, the reason for the
recommendation, and known cost or migration implications. Mark unknown prices as estimates or
unknowns; do not imply that a recommendation is already selected.

State project-wide defaults and data ownership explicitly: identify each source of truth, what
data it owns, and what supporting stores or services may and may not own. Map components to
the initial delivery or a later concrete need, with the condition for introducing them. A later
need can be a later unit in the same milestone; this does not change Engineering's flow-coverage
rules. For deferred safeguards, state the interim boundary and the release or usage gate that
must hold until those safeguards are verified. Do not prescribe infrastructure for speculative
needs.

### 3. Plan against the five pillars

Use the five pillars below as design prompts. For each, state the proposed approach, the risk
it addresses, and what is deliberately deferred. Tailor depth to the product stage and mark a
pillar or concern not applicable only with a reason.

1. **Infrastructure & hosting** — deployment shape, environments, stateful services, backups,
   access to production, and relevant traffic or availability assumptions.
2. **Code quality & testing** — component boundaries, core logic versus adapters, contracts
   between components, the critical paths to test, and how the design avoids costly coupling.
3. **Security & data** — data classification and ownership, authentication and authorization
   boundaries, secrets, third-party and AI data flows, and relevant retention or deletion needs.
4. **Observability & cost** — what must be measured to know critical flows work, where failures
   will surface, major recurring or usage-based costs, and the controls or thresholds to review.
5. **Failure & rollback** — likely dependency and data failures, safe retry or recovery behavior,
   backup/restore and deployment rollback approach, and who needs to act when recovery is manual.

Always ask about analytics; it is part of the long-term plan even when setup waits. Agree with
the user which metrics matter, starting with the spec's hypothesis metric, and who or what reads
each one: every planned event must feed a named metric, report or decision. Recommend a tool for
those metrics (for example PostHog or Mixpanel); if the user wants to decide later, record
"choose before real users" instead of inventing one. Record the PII rules for event data (what is
never sent, what is hashed or truncated, such as user IDs, emails, free text and IP addresses),
applied through the tool's own settings and filtering hook where available. Record when it must
be live: by default, events behind the hypothesis metric arriving before real users. Setting up
accounts can wait until then.

Session replay and acquisition tracking are not defaults. Recommend replay only where it would
answer a real question (complex UI flows, unexplained drop-off), and record its masking,
exclusions, access, retention, disclosure and consent; it stays off for real users until those
are verified. Plan acquisition tracking for when there is traffic to attribute, usually launch.
Do not assume scrubbed data is anonymous or legal requirements are satisfied; record material
unknowns and required review.

Do not turn every checklist row into a new service or process. State the minimum adequate
approach for the current stage and name the condition that would justify strengthening it.

#### Risk profiles and safeguards

Identify and discuss relevant product characteristics, using the product spec if available but
also assessing the actual scope and data flows independently. Examples include generative AI,
personal or sensitive data (including health information), healthcare workflows, payments,
and decisions with consequential effects on people. Profiles overlap, are not exhaustive, and
do not by themselves establish legal obligations. Ask targeted questions about unknown data,
users, jurisdictions, providers, and intended use where these affect the assessment.

For each applicable profile, record the use case and data involved, potential harms, applicable
requirements or unresolved questions, and safeguards in the architecture plan. Profiles are a
cross-cutting lens on the five pillars, not an additional pillar: keep the profile summary
concise and reference details recorded under the relevant pillars, risks or deferred work
instead of duplicating them. Distinguish:

- controls needed before development, testing with real data, an initial release, or another
  specific use; and how each will be verified;
- controls that can safely wait, their interim boundary, concrete activation or release gate,
  owner, and revisit trigger.

For generative AI, discuss data sent to providers, retention and training terms, privacy, output
failure and misuse, and an evaluation approach proportionate to the use case before affected
use; identify coverage or process that can grow later. For sensitive or regulated data, discuss
classification, minimization, access, retention, providers and jurisdiction-specific
obligations as applicable. Mark obligations and provider terms unverified until confirmed; flag
when qualified legal or domain advice is needed. A user-approved deferral cannot override an
existing guardrail or allow a blocked use before its prerequisites are verified. If an unknown
could change a necessary control, keep the affected use gated until resolved.

### 4. Surface and resolve consequential decisions

List decisions that constrain multiple components or are expensive to change, such as data
ownership, identity, sync, trust boundaries, or deployment shape. For each, explain the options,
tradeoffs, recommendation, confidence, and cost of changing it later.

Include an **Existing Technology Stack Findings** section and a **Proposed Technology Stack**
table covering the frontend framework, backend framework/runtime, hosting/deployment, database,
authentication, AI/model integration, and observability/analytics when applicable. For each
applicable layer, state what the codebase currently uses (with evidence or "none found"), what
you recommend, a credible alternative, fit/tradeoff, and cost assumption or unknown. Explain
why you recommend retaining or changing the existing choice.

Present material architecture forks and the proposed stack to the user and explicitly ask for
approval or changes. Do not mark the plan Approved or hand it to `product-engineering` until the
user approves the stack and all blocking decisions. Record approved choices and unresolved
questions in the plan. Record decisions requiring a durable decision record as ADRs through
`product-engineering`; do not duplicate ADRs in this plan.

### 5. Check coherence and right-size the plan

Walk the critical journeys through the diagram. Confirm that each data flow has a clear owner,
each external dependency has a defined boundary, and failures or sensitive operations have an
appropriate response. Call out contradictions, unowned responsibilities, and risks that testing
or a launch audit cannot fix after the fact.

Prefer the simplest design that meets the stated stage and constraints. For uncertain or
reversible choices, prefer a small validating step over a commitment. Be explicit about what
does not need to be decided yet.

### 6. Deliver and hand off

Write the initial proposal to `specs/product/architecture-plan.md`. For a checkpoint, preserve
the approved baseline and add a dated **Architecture Impact Review**: what changed, which pillars
and decisions are affected, and whether the baseline remains valid. Mark the review proposed
until approved; do not mark the existing approved baseline proposed or replace it with an
unapproved decision. Do not rewrite an approved ADR; create a superseding ADR when needed.

Use `templates/ARCHITECTURE_PLAN_TEMPLATE.md`. Write the initial plan or checkpoint review as
Proposed, then present:

1. the system diagram and its plain-language explanation;
2. the five-pillar summary and the risks that need attention first;
3. the verified existing stack findings, followed by the proposed technology stack, alternatives,
   reasons to retain/change the current choices, and cost assumptions;
4. consequential decisions, alternatives, and open questions;
5. what is intentionally deferred and the trigger to revisit it.

Pause and ask the user to approve or change new or changed material decisions. For an initial
plan, ask for approval of the proposed stack and update the plan status to Approved after
approval. For a checkpoint, record approval on the review; retain unchanged approved choices
without asking again. When a review changes a decision, update the plan's current effective
decision summary after approval and retain the prior decision and rationale in the dated review
or an existing ADR. Tell the user the approved plan path and unresolved questions, and recommend
running `/product-engineering` when they are ready to plan implementation. Stop; do not invoke
the other skill automatically.
Make clear which decisions are approved now, which are approved for a later concrete need, and
which are only options. Engineering maps them into milestones without re-approving settled
choices or building deferred components early.

After implementation, `product-engineering` updates the living `specs/engineering/` description
to reflect what actually shipped. Keep the approved target and a concise, dated implementation
status in `specs/product/architecture-plan.md`; distinguish evidence recorded at planning time
from current reality. A deferred component is not a deviation simply because it is unbuilt.
Update status when it changes, and use an impact review for material changes to decisions.

## Checkpoint Triggers

Re-run a focused impact review when any of these changes:

- product stage, expected scale, or availability needs;
- data sensitivity, ownership, retention, or access patterns;
- an important integration, model provider, or deployment boundary;
- a critical user journey's failure or recovery requirements;
- recurring or variable operating cost beyond the agreed assumptions;
- a foundational architectural decision or its enforcement mechanism.

Routine changes that stay within established boundaries need no architecture checkpoint.
