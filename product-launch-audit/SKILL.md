---
name: product-launch-audit
description: >-
  Audit an app (built with or without product-engineering, including Replit/Lovable/Bolt
  prototypes) against five pillars before going live: infrastructure, code quality,
  security, observability and cost, failure and rollback. Runs a repo scan, then
  produces a status table per pillar and findings split into fix-now, needs-your-credentials,
  and not-a-code-problem. Use before launch, before showing investors, or when asked
  "is this safe to ship?"
---

# product-launch-audit

A pre-launch check of an existing codebase. Repeat it when launch conditions or material risks
change. For per-unit checks during a build, use `product-engineering`.

## Inputs

- **Stage**: Finding Product-Market-Fit (PMF), Growth or Scale. Use an already confirmed stage
  from the approved architecture plan if available; otherwise briefly explain all three using
  the [stage definitions](CHECKLIST.md#product-stages), then ask the user to confirm one. The
  stage decides the checklist baseline, but actual risk may require stronger controls earlier.
- **Path**: the repo to audit (default: current directory). It does not need to be a git repo or use product-engineering.

## Steps

1. **Establish context.** Read the approved architecture plan and shipped engineering specs if
   present, including risk profiles, access boundaries, operating assumptions and release or
   usage gates. Independently identify relevant risks from actual use cases and data flows,
   even without a plan. The plan is intent, not evidence that a control shipped.
2. **Scan.** Run the mechanical checks and read the JSON:
   ```bash
   python .claude/skills/product-launch-audit/scripts/audit_repo.py <path>
   ```
   Statuses: `pass`, `warn`, `fail`, `manual` (verification needed). The script excludes all
   `.env*`, `*.pem`, `*.key`, `secrets/`, `.agent/guardrails.json`, symlinks, and common generated
   directories and lockfiles. Ask the user to check excluded environment files and credential
   handling privately; never ask for or display secret values. Service detection cannot see
   excluded files, so confirm the integration inventory with the user or safe configuration.
3. **Verify heuristics.** Treat matches, no matches, and dependency or configuration presence
   as leads, not proof. Verify actual route access and ownership, rate-limit enforcement,
   model-tool validation and permissions, CI scanning, logging, and RLS policies where
   applicable. Confirm or dismiss potential secret hits without exposing values. No match does
   not prove absence; unsupported frameworks or integrations require manual review.
4. **Judge the checklist.** Apply only the chosen stage and preceding stages, then assess each
   row's applicability. The scanner emits leads for all stages, so do not roll up unrelated
   checks. Check the code and operational evidence, not the framework's reputation; cite file
   and line for code findings and describe the evidence needed for external or manual findings.
5. **Handle manual rows.** Ask the user or report them as unverified. For paid services, prefer
   a verified provider-enforced hard cap and scoped key. Where no provider cap exists, assess an
   application limit's coverage and residual risk, including bypass through direct key use,
   concurrency and billing lag; alerts alone are not a cap. Do not claim a hard bound without
   evidence. For applicable risk profiles, verify evidence for safeguards and release/usage gates
   needed for the proposed use; report missing, unresolved or unverified prerequisites and
   prevent a readiness claim for the affected use. For AI, check whether evidence of the
   planned, proportionate evaluation exists; do not conduct or claim an independent quality
   evaluation. Flag when qualified legal or domain review is needed rather than claiming
   compliance. The user checks provider settings; agents never access production credentials.
6. **Report** using the format below.

## Report format

```markdown
# Launch audit: <app>, stage <PMF|Growth|Scale>

| Pillar | Status | What's needed |
| :--- | :--- | :--- |
| Infrastructure & hosting | ✅/⚠️/🔴 | ... |
| Code quality & testing | | |
| Security & data | | |
| Observability & cost | | |
| Failure & rollback | | |

## Blockers
<🔴 items, with file:line for code or evidence needed for manual/infrastructure findings>

## Findings
**Fix directly (AI can do it):** ...
**Needs a credential or account from you first:** ...
**Not a code problem (you do it):** ... (rollback dry run, who to call, spend cap, audit)
```

Rules:
- 🔴 = a confirmed applicable failure or security gap. ⚠️ = an applicable warning or unverified
  manual check. ✅ = all applicable rows verified; explicitly list non-applicable rows and reasons.
- Explain the hosting model's tradeoffs even when it meets the requirements; serverless or
  cold starts alone are not failures.
- Any 🔴 in Security & data is a launch blocker. Say so first.
- Report only. Do not fix anything unless the user asks.
- Independently evaluating AI output quality is out of scope; report whether required evaluation
  evidence is present or unverified, without treating its existence as proof of quality.
- AI runtime locks (least-privilege tools, argument validation, approval on irreversible actions,
  personal-data minimization and redaction or an approved and verified identifying-data flow,
  and untrusted text) apply only when the app calls a model. Existing stricter project locks
  remain applicable. Their dev-time counterpart, locks on the agent that builds the app, lives
  in `product-engineering`.
