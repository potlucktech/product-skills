# product-architecture

Creates a founder-readable architecture baseline before implementation, then checks it again
when meaningful changes could invalidate it. It uses five architecture pillars to plan the system
instead of auditing a running app. It is not a living specification of shipped behavior: detailed current
behavior belongs in `specs/engineering/`. The plan records approved intent and a concise dated
implementation status. It proposes a concrete technology stack and pauses for your approval
before marking the plan approved.

## Flow

```text
Product scope → Architecture baseline → Product-engineering milestone plan
                       ↑
      consequential feature or project checkpoint
```

The initial plan covers the system shape, critical data flows, and decisions across:

- infrastructure and hosting;
- code quality and testing;
- security and data;
- observability and cost;
- failure and rollback.

It names what needs to be decided now, what can stay flexible, and what change should trigger
another review. It names project-wide defaults, data ownership, and concrete later needs without
designing speculative scale infrastructure. A checkpoint is a focused architecture impact
review, not a full rewrite.

## What You Get

- `specs/product/architecture-plan.md`, a proposed design kept distinct from the architecture
  that has actually shipped;
- a system-context diagram and plain-language explanation;
- verified findings about the existing stack (or an explicit note that none was found);
- a recommended technology stack with alternatives and cost assumptions for you to approve;
- which components are needed now, approved for a concrete later need, or only options;
- risk profiles and safeguards, including what is needed before a particular use and what can
  safely wait with a clear boundary and trigger;
- interim boundaries and release gates for safely deferred controls;
- stage-appropriate risks, decisions, assumptions, and revisit triggers;
- a recommendation to run `/product-engineering` when ready, without invoking it automatically.

Budgets are stated in USD by default unless you explicitly specify another currency.

Use [SKILL.md](SKILL.md) for the workflow and
[ARCHITECTURE_PLAN_TEMPLATE.md](templates/ARCHITECTURE_PLAN_TEMPLATE.md) for the output.

## Works With

- [product-scoping](../product-scoping/README.md) defines user outcomes, scope, and flows.
- [product-engineering](../product-engineering/README.md) turns the approved architecture and
  product scope into buildable units and keeps the shipped engineering specs current.
- [product-launch-audit](../product-launch-audit/README.md) checks an existing app before launch.
