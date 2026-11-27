# Analytics: planned metrics, set up when needed

The approved architecture plan's **Analytics** section decides what is measured: the metrics that
matter (the hypothesis metric first), who or what reads each, the tool, the PII rules for event
data, and when it must be live. Build only what it plans. **No event without a reader**: every
event feeds a named metric, report or decision, and an event whose metric is dropped is removed in
the same unit, with its tests. If the plan has no Analytics section, ask the user to run
`/product-architecture` for a focused review rather than inventing metrics.

Account setup is the user's choice: now, in Phase 0, or later. Later is a normal choice, not an
exception. The hard gate is the **P0 checkpoint**: the hypothesis-metric events must be arriving
before real users.

`CONFIG.md` keys: `ANALYTICS_SETUP` (`now` or `later`), `ANALYTICS_PLATFORM` (the tool),
`ANALYTICS_ACCESS` (the MCP or API used to query it), `ACQUISITION_ANALYTICS` (blank unless
planned), `ANALYTICS_CATALOGUE` (path of the event catalogue).

| When | What happens |
| :--- | :--- |
| 0 Setup | Ask: set up analytics accounts now, or later? Record the answer in `ANALYTICS_SETUP` |
| 1 Plan | Set up now: the skeleton installs the tool. Later: plan one instrumentation unit as the last P0 unit. Only units that produce a planned metric list events |
| 3–4 Tests first, build | Events go through one thin `track()` wrapper that applies the PII rules; each joins the catalogue with its metric |
| 5 Verify | `[Instrumentation]` passes offline; `[Live]` arrival passes, or is reported unverified while accounts aren't set up |
| P0 checkpoint | Hypothesis-metric events confirmed arriving before real users |

## Phase 0: set up now or later (human only)

Ask once: "Set up analytics accounts now, or later?" Either answer is fine; record it as
`ANALYTICS_SETUP` in `CONFIG.md`.

When accounts are set up (now, or before the instrumentation unit): separate **dev** and **prod**
projects in `ANALYTICS_PLATFORM`, each with its own key. The dev key goes in the local `.env`, the
prod key in the host's secret settings. The agent never reads either; code picks the key by
environment. Also request a **read-only credential for the dev project** (e.g. a Mixpanel service
account limited to the dev project, a PostHog personal key scoped to query) in `.env`, so `[Live]`
tests can read back what arrived. The ingestion and query hosts go in `LIVE_ALLOWED_HOSTS`. Add a
prod `ACQUISITION_ANALYTICS` property only when the plan schedules acquisition tracking. Never
work around a missing credential.

## Phase 1: where analytics goes in the plan

- **No metrics planned:** no analytics code, catalogue or tests.
- **`ANALYTICS_SETUP: now`:** the walking skeleton installs the tool, the `track()` wrapper with
  the PII rules, and the test kit. Units that produce a planned metric emit its events as they are
  built.
- **`ANALYTICS_SETUP: later`:** plan one `infra` unit, **Analytics instrumentation**, as the last
  P0 unit (right before the P0 checkpoint). It installs the tool, the wrapper with the PII rules
  and the test kit, adds the events behind the hypothesis metric to the P0 journeys, and proves
  they arrive. Earlier units emit no events. P1 and P2 units that produce a planned metric emit its
  events as they are built. If the plan still says "choose before real users", ask the user to
  choose the tool through a focused `/product-architecture` review before this unit starts; at its
  start, ask the user to set up the accounts.
- **Session replay:** only when the plan includes it. Configure it with the planned masking and
  exclusions, keep it off for real users until its gates are verified, and give each UI unit an M
  or T scenario checking its sensitive fields are masked.
- **Reporting unit:** optional, only when the plan names reports or dashboards the tool doesn't
  provide out of the box. If present, it comes last and lists what it builds instead of events.

## The `track()` wrapper and test kit

Built by whichever unit installs the tool:
- a thin `track()` wrapper over the tool's SDK, so vendor calls live in one place. It applies the
  plan's PII rules, using the tool's own filtering hook (e.g. `before_send`) and settings (e.g.
  dropping IP addresses) where available;
- an event catalogue at `ANALYTICS_CATALOGUE`: each event, its properties, and the metric it
  feeds. `track()` raises on unknown events or properties in dev/test and drops them in prod;
- a fake sink with an `assert_tracked(event, **props)` helper;
- a test that feeds synthetic PII through `track()` and asserts it is removed, hashed or truncated
  as the plan says;
- a test that every contract's Instrumentation events match the catalogue both ways;
- a live helper: runs a flow with the analytics hosts allowed through, tags events with a run id,
  then polls the dev project through the read-only credential until each expected event arrives
  (or times out). Skips and reports without the dev key.

When a third-party browser library is integrated, vendor a pinned copy served by the app so browser
tests run it with endpoints intercepted. Blocking all network hides "library never initialised"
bugs.

## Unit contracts (Part C)

- Section C lists the events the unit emits (name, trigger, properties, metric), or `None`.
  Only units that produce a planned metric list events.
- A unit that lists events has an `[Instrumentation]` T scenario: drive its flows and assert each
  event and its properties through the fake sink (server) and intercepted analytics requests
  (browser). New events join the catalogue in the same unit.
- Once accounts are set up, it also has a `[Live]` T scenario (`(live)`): the same flow through
  the live helper, asserting each event arrived in the dev project. Before then, the contract says
  analytics isn't set up yet; do not claim delivery.
- `check_loop.py plan` fails a contract that lists events without an `[Instrumentation]` T
  scenario, and a reporting unit that isn't last.

## Verify (Phase 5)

- **Offline**: the `[Instrumentation]` T scenario passes and the catalogue is in sync. A new
  catalogue property is checked against the plan's PII rules.
- **Live**: once accounts are set up, the `[Live]` T passes inside `TEST_COMMAND`. Before then, a
  skipped `[Live]` test is reported as unverified, not passed.
- **No read-only credential yet?** If the approved `ANALYTICS_ACCESS` provides a narrowly scoped
  dev read-back without one, the orchestrator queries it for the run id and gives the verifier the
  result, labelled semi-automated.

## P0 checkpoint

After the last P0 unit, confirm the hypothesis-metric events are arriving in the dev project, with
the prod key configured in the host. Until they are, report measurement as blocked: the checkpoint
is not complete, P1 work doesn't start, and the app isn't ready for real users.
