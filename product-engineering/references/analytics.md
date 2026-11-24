# Analytics: instrumented by default

Every journey unit ships the analytics events for what it builds. The milestone's last unit turns those events into a dashboard, reports, or saved queries. Follow the approved architecture for the analytics mechanism; where it uses vendor projects, separate dev and production data so test traffic never pollutes real metrics. Session replay is a separate, opt-in decision, not a prerequisite for analytics.

`CONFIG.md` keys: `ANALYTICS_PLATFORM` (where events go), `ANALYTICS_ACCESS` (the MCP or API used to query it), `ACQUISITION_ANALYTICS` (prod acquisition property), `ANALYTICS_CATALOGUE` (path of the event catalogue).

| Phase | What happens |
| :--- | :--- |
| 0 Setup | A human configures approved services, or records an explicitly approved deferral |
| 1 Plan, skeleton unit | Approved analytics seam and offline test kit; replay only when approved and gated |
| 1 Plan, every journey unit | Contract section C lists events; an `[Instrumentation]` T scenario asserts them |
| 3 Tests first | The `[Instrumentation]` test is written and fails |
| 4 Build | Events go through one `track()` seam; new events join the catalogue |
| 5 Verify | `[Instrumentation]` passes offline; the applicable live check passes or an approved deferral is reported |
| P0 checkpoint | Hypothesis-metric events confirmed arriving |
| Last unit (reporting) | Dashboards, reports, saved queries |

## Phase 0: accounts and keys (human only)

For an approved vendor that requires projects, use separate **dev** and **prod** projects in `ANALYTICS_PLATFORM`, and a prod `ACQUISITION_ANALYTICS` property if the approved approach requires one, each with its own key. The dev key goes in the local `.env`, the prod key in the host's secret settings. The agent never reads either; code picks the key by environment. Also request a **read-only credential for the dev project** (e.g. a Mixpanel service account limited to the dev project, a PostHog personal key scoped to query) in `.env`, so the `[Live]` tests can read back what arrived. The analytics ingestion and query hosts go in `LIVE_ALLOWED_HOSTS`.

The user may explicitly defer setup; record this in `CONFIG.md` or another project setup record, then carry it into the milestone and affected contracts along with offline coverage, the missing live checks, and the gate before reports or real-user use that depends on them. Do not send real-user data or claim live verification while setup is deferred. Otherwise stop and ask for required credentials; never work around a missing one. First-party analytics does not require vendor projects or replay.

## Skeleton unit

- Initialize the approved analytics mechanism when configured. When setup is explicitly deferred, use the offline seam and fake sink without live delivery; report the missing live verification.
- Initialize replay only if it is separately approved and the appropriate privacy, masking, consent and real-user gates in the architecture are met. Otherwise leave it disabled.
- **Analytics test kit**:
  - an event catalogue at `ANALYTICS_CATALOGUE`: every event name with its required properties and types. `track()` raises on unknown events or properties in dev/test and drops them in prod;
  - a fake sink with an `assert_tracked(event, **props)` helper;
  - a browser fixture that intercepts configured analytics endpoints and decodes what the page sends, or asserts the offline seam when no vendor is configured;
  - a test that every contract's Instrumentation events match the catalogue both ways;
  - a test that every catalogue event is asserted by at least one test;
  - for a vendor integration, a live helper: runs a flow with the analytics hosts allowed through, tags events with a run id, then polls the dev project through the read-only credential until each expected event arrives (or times out). Skips and reports without the dev key.
- When a third-party browser library is actually integrated, vendor a pinned copy served by the app so browser tests run it with endpoints intercepted. Blocking all network hides "library never initialised" bugs.

## Unit contracts (Phase 1, Part C)

- Section C lists the events the unit emits: name, trigger, properties.
- Journey units: one view event and one primary-action event per capability. P0 journeys also emit the events behind the spec's hypothesis metric.
- Every journey unit has an `[Instrumentation]` T scenario: drive the unit's flows and assert each listed event and its properties through the fake sink (server) and intercepted analytics requests or the offline seam (browser). New events go into the catalogue in the same unit.
- For an approved vendor integration, every journey unit also has a `[Live]` T scenario (`(live)`): the same flow through the live helper, asserting each listed event arrived in the dev project with its properties. Mark it not set up yet when the user has approved deferral; do not claim delivery.
- The reporting unit lists the dashboards and queries it builds instead of events.
- `check_loop.py plan` fails a journey unit with no events or no `[Instrumentation]` T scenario, and a plan whose last unit isn't reporting.

## Build (Phase 4)

Emit every event through one analytics seam, a single `track()` wrapper, so tests can assert events with a fake sink and no vendor SDK call is scattered through UI code. Add each new event to the catalogue with its properties.

## Verify (Phase 5)

- **Offline**: the `[Instrumentation]` T scenario passes and the catalogue is in sync.
- **Live**: for a configured free vendor, the `[Live]` T passes inside `TEST_COMMAND`. A skipped `[Live]` test blocks PASS unless the contract records the user-approved setup deferral; the verdict must name live delivery as unverified. A first-party mechanism is verified through its appropriate integration tests.
- **No read-only credential yet?** If the approved `ANALYTICS_ACCESS` provides a narrowly scoped dev read-back without one, the orchestrator queries it for the run id and gives the verifier the result, labelled semi-automated. Otherwise, a missing required credential blocks verification unless setup is explicitly deferred; never work around it.

## P0 checkpoint and reporting

- After the last P0 unit, confirm the hypothesis-metric events are arriving. If setup is deferred, report this gate as blocked; don't claim measurement readiness or proceed to P1 until the checkpoint is satisfied.
- The last unit builds the dashboard, reports, or saved queries over the events from earlier units, through the approved mechanism. Reports depending on deferred setup remain blocked.
