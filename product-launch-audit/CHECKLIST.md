# Checklist by stage

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

Each confirmed stage includes the rows of the stages before it. Use stronger controls earlier
when the actual risk warrants them. `Script` IDs are leads or mechanical evidence, not proof of
effective controls. Verify applicability and effectiveness; mark a row not applicable only with
a reason, and leave unverified controls manual.

## Finding Product-Market-Fit (PMF)

| Pillar | Row | Script |
| :--- | :--- | :--- |
| Infrastructure & hosting | Code is in a real git repo with a remote | [git_repo, git_remote] |
| | Environment files are not committed and are properly ignored; ask the user to privately check excluded files and credential handling | [env_committed, env_contents] |
| | Explain hosting tradeoffs, including serverless cold starts, availability, recovery and cost, against the agreed requirements; don't assume dedicated hosting is required | [hosting_defaults] |
| | Database backups stored outside the volume and account the app and agent can reach; one restore done | [backups] |
| | Rate limit on public and login endpoints | [rate_limit] |
| Code quality & testing | At least one test on the critical flow | [tests_exist, critical_flow_covered] |
| | Assess tech debt by its impact on critical flows, security, reliability, and the next likely change; prioritize launch-threatening risks and defer harmless cleanup | judgment |
| | Independently review high-risk launch paths, including relevant failure and abuse cases, regardless of who or what wrote the code | judgment |
| | *If generative AI is used:* check evidence of the planned, use-appropriate output evaluations and their release gates; report missing or unverified evidence without independently judging output quality | judgment |
| Security & data | No hardcoded secrets | [secrets_in_source] |
| | Protected data and operations enforce appropriate authentication, authorization and ownership; deliberately public or anonymous endpoints have appropriate abuse, privacy and rate-limit controls | [endpoints_without_auth] |
| | Every deploy and cloud token scoped to one environment and the actions it needs; production tokens only in the host's dashboard | [infra_token:*] |
| | Verify access controls for every relevant data store and table, including ownership isolation; use RLS where applicable or equivalent enforced application/data-access boundaries | [rls] |
| | Assess local user data against approved storage boundaries, sensitivity, device access and retention; explicitly approved local drafts are not inherently a failure | judgment |
| | *If customer data reaches third-party AI:* minimize data, remove direct identifiers and sensitive context where possible, assess re-identification, verify provider training and retention terms, and verify required disclosure, consent and approval before use | [ai_data_handling] |
| | Assess applicable risk profiles and verify required safeguards and use-specific gates against evidence; flag unresolved legal, provider or domain questions for qualified review, not assumed compliance | judgment |
| | *If session replay is enabled:* verify sensitive-content masking/exclusion and settings, access, retention, disclosure and consent as applicable; test with synthetic inputs and keep replay disabled for real users until its approved privacy gate passes | judgment |
| | *If the app calls a model:* tools are least-privilege (nothing the feature doesn't need, no delete or send it doesn't use) | [ai_tool_review] |
| | *If the app calls a model:* every tool argument is schema-validated against an allowlist | [ai_validation] |
| | *If the app calls a model:* irreversible actions (send, delete, pay, publish) need approval bound to the exact action | manual |
| | *If the app calls a model:* minimize personal data and redact identifiers unless needed for the approved use; before sending necessary identifying data, verify the user-approved data flow, applicable privacy and security safeguards, provider terms, and required legal or domain review | [ai_pii_redaction] |
| | *If the app calls a model:* retrieved and uploaded text is labeled untrusted, and no feature combines private data + untrusted content + a way to send data out | judgment |
| Observability & cost | Verify that errors in critical flows can be detected and investigated; flag absence of a recognized tracker for manual review, not automatic failure | [error_tracker] |
| | Analytics shows where users drop off | judgment |
| | Monthly cost known | [monthly_cost] |
| | For each paid API: verify key scope, spend alerts and a provider-enforced hard cap where available. If unavailable, assess application-side limits and residual exposure (direct key use, concurrent requests, delayed billing); alerts alone are not caps. Escalate an unbounded risk before launch | [paid_key:*] |
| Failure & rollback | Manual rollback done once as a dry run | [rollback_dry_run] |
| | Named person to call if the API or database goes down | [runbook] |

## Growth

| Pillar | Row | Script |
| :--- | :--- | :--- |
| Infrastructure & hosting | Branch protection; separate staging environment | [ci], [staging] |
| Code quality & testing | Tests on the top flows; PR review; CI/CD | [ci] |
| | Review consequential changes consistently and track recurring tech debt | judgment |
| Security & data | Secrets audited and rotated; role-based access for humans | judgment |
| | CI runs a secret scanner | [ci_secret_scan] |
| | Dependencies reviewed; lockfile committed | [lockfile, dependency_audit] |
| Observability & cost | Uptime monitoring; alerts to Slack; cost by feature | judgment |
| Failure & rollback | Written runbooks; incident docs | [runbook] |

## Scale

| Pillar | Row | Script |
| :--- | :--- | :--- |
| Infrastructure & hosting | Granular permissions for AI agents | [agent_permissions] |
| Code quality & testing | Maintain a prioritized tech-debt roadmap; use deeper threat modeling or specialist review where system risks warrant it | judgment |
| Security & data | Data governance; retention policy; third-party audit | judgment |
| Observability & cost | Cost governance across model tiers | judgment |
| Failure & rollback | Incident review process | judgment |
