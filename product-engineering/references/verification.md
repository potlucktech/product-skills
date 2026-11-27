# Phase 5: verifier steps

For the `loop-verifier` / `loop-verifier-strict` subagent. You get the unit contract path, the `git diff` of the unit's changes, and the `check_loop.py` JSON. You read and run; you never edit. Audit what you observe against the contract, not what the maker says it did.

## 1. Mechanical CI gate (deterministic)

Run `python .claude/skills/product-engineering/scripts/check_loop.py NN` and inspect the JSON:
- Test suite exit code and summary, across every automated tier (unit, integration, end-to-end, free live).
- **Skipped free live tests**: any `skipped: no dev key` is a finding at certainty 7+, unless the contract records a user-approved setup deferral, or it is an analytics test while `ANALYTICS_SETUP` is `later`. In that case explicitly report live delivery as unverified and preserve its release gate.
- Linter and formatter exit codes.
- Full mapping of T1..Tn tokens to tests. Zero missing tokens.
- `hygiene`: likely hardcoded secrets in changed files (fails the gate), and route files that mention no auth (heuristic: read each and confirm or dismiss it with file:line).
- `guardrails`: config present, adapters wired, no protected or append-only path edited, a new ADR for any guardrail-config or design-system change, and the privacy gates (fail the gate). `privacy_warnings` lists real-looking emails and phones to confirm or dismiss with file:line.
- `diff`: changed source files, and test files that lost assertions or gained skips, sleeps, or timeouts.

## 2. Manual E2E walkthrough audit

- Step through each M1..Mk scenario.
- **Reachability**: a step a person can't perform once this unit ships (it needs a later unit, an account or key the human doesn't have, or a particular time of day without a dev override) is a finding at certainty 7+, not "pending human". "Pending human" is only for steps a person can do but you can't, such as a check on a real phone.
- Confirm UI components, responsive breakpoints, error recovery states, and navigation work as specified.
- Apply the `VIEWPORT_BREAKPOINTS` and `PARITY_REFERENCE_URL` rules in `CONFIG.md`.
- Instrumentation (units that list events): the `[Instrumentation]` T scenario covers events offline, and each event names a planned metric. Once analytics accounts are set up, `[Live]` tests cover arrival in the dev project; before then, report live delivery unverified. A new catalogue property is checked against the plan's PII rules. If read-back is semi-automated, use the orchestrator's result and say so in the verdict ([Analytics](analytics.md)).
- Paid `[Live]` walkthroughs: confirm each states its cost and when it runs. Don't run them; they run at the Phase 6 checkpoint.

## 2b. Tier audit

- Every journey unit has an end-to-end happy-path T, and it really drives the app in a browser (not a route call dressed up as e2e).
- Every outside service the unit calls has a live check: a `[Live]` T if free, a `[Live]` M with a cost if paid.
- No unit, integration or end-to-end test reaches the network beyond the local machine; free live tests reach only `LIVE_ALLOWED_HOSTS`; no paid key is read by any test.

## 3. Test fidelity audit

- Assertions are substantive, not tautological or hollow.
- Error branches assert status codes, error types, and error messages.

## 4. Semantic acceptance criteria audit

Check every `Acceptance Criteria` checkbox against the actual code and runtime behavior.
Check the unit's relevant architecture boundaries and release/usage gates against the diff and
tests. Consult its linked architecture plan when the unit touches a material decision or
change; flag an unapproved conflict or changed boundary instead of treating planned future
components as missing implementation.

## 5. Test edits and scope drift

- For each file in `diff.test_files_to_justify`, every removed or loosened assertion traces to a contract line that changed. A test edited to fit the code, with no contract change behind it, is a finding.
- **Scope creep**: any hunk in `diff.source_files` that no contract line asks for (a bug fix riding along in a test-only change counts).
- **Missing requirement**: any contract line with no code or test behind it.

## 6. Guardrails audit

- Read the unit's **Risk** and Guardrails ADR. Confirm each lock for that level exists ([Guardrails](guardrails.md)), and that its `[Guardrail]` / `[Abuse]` tests assert the block (status code, error, or no side effect), not just that the code path runs.
- Diff-review any change to guardrail config or protected paths against the ADR that justifies it.
- High risk: confirm the work ran without real credentials.

## 7. Findings and verdict

Each finding: file:line, the quoted code line it rests on, expected vs. observed, and a certainty from 1 to 10.
- 7+ blocks a PASS (5+ for high-risk units).
- 4–6 go under **Unverified**: listed, non-blocking.
- Below 4: dropped.

Return this table, then the findings:

```markdown
### Unit NN — <Unit Name> Verification Verdict
| Criterion / Gate | Status | Evidence |
| :--- | :--- | :--- |
| Automated Tests (T1..Tn) | PASS | n/n mapped and passing green |
| Manual E2E Tests (M1..Mk) | PASS | All browser walkthroughs verified |
| CI & Linter Gates | PASS | Tests green; 0 lint/format warnings |
| Seam & Architecture Invariants | PASS | Logic isolated in core; scoping verified |
| Test tiers | PASS | Required tiers as contracted; e2e happy path drives the browser; any service not set up yet explicitly reported |
| Instrumentation | PASS | No events, or offline T passes, catalogue in sync and PII rules hold; live delivery verified, or reported unverified while accounts aren't set up |
| Semantic Acceptance Criteria | PASS | All bullet criteria verified |
| Guardrails (risk: low/medium/high) | PASS | Locks for this level present; negative tests pass; config unchanged or ADR'd |
| Test Edits & Scope Drift | PASS | Every test edit traced to the contract; no unrequested changes |
| **OVERALL VERDICT** | **PASS** | **Ready for living spec sync** |
```
