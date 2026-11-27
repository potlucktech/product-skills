#!/usr/bin/env python3
"""Deterministic repo scan for the `product-launch-audit` skill.

Works on any folder (git repo or not). Emits JSON evidence; the LLM layer turns it
into the pillar report. Statuses: pass | warn | fail | manual (a human must check).

Usage:
    python audit_repo.py [path]     # default: current directory
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", ".expo", "coverage"}
SKIP_FILES = re.compile(r"(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|uv\.lock|poetry\.lock|\.min\.js|\.map)$")
CODE_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".yml", ".yaml", ".toml", ".env", ".sql", ".sh", ".md", ".txt")

SECRET_RES = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"(?i)(?:api[_-]?key|secret|token|passwd|password|service[_-]?role)\w*\s*[:=]\s*['\"][A-Za-z0-9_\-./+=]{16,}['\"]"),
]
SECRET_IGNORE = re.compile(r"(?i)process\.env|os\.environ|getenv|import\.meta\.env|example|your[_-]|xxx|changeme|placeholder|<[^>]+>|\$\{")

ROUTE_RE = re.compile(
    r"\b(?:app|router|api)\.(?:get|post|put|patch|delete|all)\(|@(?:app|router|api)\.(?:get|post|put|patch|delete)\(|"
    r"export\s+(?:async\s+)?function\s+(?:GET|POST|PUT|PATCH|DELETE)\b"
)
AUTH_RE = re.compile(
    r"(?i)auth|session|getUser|currentUser|clerk|jwt|verify_token|Depends\(|login_required|requireUser|bearer|middleware"
)

AI_SDKS = ("openai", "anthropic", "@ai-sdk", "langchain", "llama-index", "llama_index", "google-generativeai", "@google/genai", "litellm", "mistralai", "cohere")
TOOL_USE_RE = re.compile(r"(?i)\btools\s*[=:]|tool_use|tool_calls|function_call|@tool\b|mcp\.tool|server\.tool\(|createTool\(")
POWER_RE = re.compile(r"(?i)\b(?:delete|drop|truncate|rmtree|unlink|send_?mail|send_?email|sendmessage|exec|subprocess|os\.system|charge|refund|transfer|publish)\b")
VALIDATION_LIBS = ("pydantic", "zod", "jsonschema", "ajv", "valibot", "yup", "marshmallow")

DEP_FILES = ("package.json", "requirements.txt", "pyproject.toml", "Pipfile", "go.mod", "Gemfile")
ERROR_TRACKERS = ("sentry", "bugsnag", "rollbar", "honeybadger", "datadog", "logrocket", "highlight.run")
RATE_LIMITERS = ("express-rate-limit", "rate-limiter-flexible", "@upstash/ratelimit", "slowapi", "flask-limiter", "django-ratelimit", "fastapi-limiter", "rate_limit", "ratelimit")
LOCKFILES = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "uv.lock", "poetry.lock", "Pipfile.lock", "go.sum", "Gemfile.lock")

# Usage-billed services: (dependency names, env var names). A leaked or looping key bills until someone notices.
PAID_SERVICES = {
    "OpenAI": (("openai",), ("OPENAI_API_KEY",)),
    "Anthropic": (("anthropic",), ("ANTHROPIC_API_KEY",)),
    "Google Gemini": (("google-generativeai", "@google/genai", "google-genai"), ("GEMINI_API_KEY",)),
    "ElevenLabs": (("elevenlabs",), ("ELEVENLABS_API_KEY",)),
    "Replicate": (("replicate",), ("REPLICATE_API_TOKEN",)),
    "Mistral": (("mistralai",), ("MISTRAL_API_KEY",)),
    "Cohere": (("cohere",), ("COHERE_API_KEY",)),
    "Twilio": (("twilio",), ("TWILIO_AUTH_TOKEN",)),
    "Google Maps": (("googlemaps", "@googlemaps"), ("GOOGLE_MAPS_API_KEY",)),
}
# Hosts and clouds: (config files, env var names). Their tokens can delete production.
INFRA_HOSTS = {
    "Railway": (("railway.json", "railway.toml"), ("RAILWAY_TOKEN", "RAILWAY_API_TOKEN")),
    "Render": (("render.yaml",), ("RENDER_API_KEY",)),
    "Vercel": (("vercel.json",), ("VERCEL_TOKEN",)),
    "Fly": (("fly.toml",), ("FLY_API_TOKEN",)),
    "Netlify": (("netlify.toml",), ("NETLIFY_AUTH_TOKEN",)),
    "Heroku": (("Procfile",), ("HEROKU_API_KEY",)),
    "Cloudflare": (("wrangler.toml", "wrangler.json", "wrangler.jsonc"), ("CLOUDFLARE_API_TOKEN",)),
    "AWS": (("serverless.yml", "samconfig.toml", "cdk.json"), ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")),
    "Supabase": (("supabase/config.toml",), ("SUPABASE_ACCESS_TOKEN", "SUPABASE_SERVICE_ROLE_KEY")),
    "Terraform": ((), ()),  # any *.tf file
}
CI_FILES = (".gitlab-ci.yml", ".circleci/config.yml", "bitbucket-pipelines.yml")
SECRET_SCANNERS = re.compile(r"(?i)gitleaks|trufflehog|detect-secrets|ggshield|check_loop\.py|secret[_-]?scan")
ENV_NAME_RE = re.compile(r"\b[A-Z][A-Z0-9_]{3,}\b")


def git(root: Path, *args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=60)
        return p.returncode, p.stdout.strip()
    except Exception as e:
        return 1, str(e)


def protected_path(path: Path) -> bool:
    return (
        path.name.startswith(".env")
        or path.suffix.lower() in {".pem", ".key"}
        or "secrets" in path.parts
        or (path.name == "guardrails.json" and path.parent.name == ".agent")
    )


def list_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d != "secrets" and not Path(dirpath, d).is_symlink()]
        for f in files:
            path = Path(dirpath, f)
            if not protected_path(path) and not path.is_symlink() and not SKIP_FILES.search(f):
                out.append(path)
    return out


def read(p: Path) -> str:
    if protected_path(p) or p.is_symlink():
        raise ValueError(f"Refusing to read protected or symlinked path: {p}")
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def check(pillar: str, cid: str, status: str, detail: str, **extra) -> dict:
    return {"pillar": pillar, "id": cid, "status": status, "detail": detail, **extra}


def scan_secrets(root: Path, files: list[Path]) -> list[dict]:
    hits = []
    for p in files:
        name = p.name
        if not name.endswith(CODE_EXTS):
            continue
        for n, line in enumerate(read(p).splitlines(), 1):
            if len(line) > 400 or SECRET_IGNORE.search(line):
                continue
            if any(r.search(line) for r in SECRET_RES):
                hits.append({"file": str(p.relative_to(root)), "line": n})
                break
    return hits


def scan_endpoints(root: Path, files: list[Path]) -> list[str]:
    """Files that define routes but mention no auth at all. A heuristic: review each one."""
    flagged = []
    for p in files:
        if not p.name.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".mjs")) or re.search(r"\.(test|spec)\.|test_", p.name):
            continue
        text = read(p)
        if ROUTE_RE.search(text) and not AUTH_RE.search(text):
            flagged.append(str(p.relative_to(root)))
    return flagged


def rls_gaps(files: list[Path]) -> tuple[int, list[str]]:
    created, secured = set(), set()
    for p in files:
        if p.suffix != ".sql":
            continue
        text = read(p).lower()
        created |= set(re.findall(r"create table (?:if not exists )?(?:public\.)?\"?(\w+)\"?", text))
        secured |= set(re.findall(r"alter table (?:only )?(?:public\.)?\"?(\w+)\"? enable row level security", text))
    return len(created), sorted(created - secured)


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    files = list_files(root)
    rel = lambda p: str(p.relative_to(root))
    checks: list[dict] = []

    # Pillar 1: infrastructure and hosting
    is_git = git(root, "rev-parse", "--is-inside-work-tree")[0] == 0
    if not is_git:
        checks.append(check("infra", "git_repo", "fail", "Not a git repo. Code exists only in the tool's history or local disk."))
    else:
        has_commits = git(root, "rev-parse", "HEAD")[0] == 0
        _, remotes = git(root, "remote")
        checks.append(check("infra", "git_repo", "pass" if has_commits else "warn", "Git repo" + ("" if has_commits else " with no commits")))
        checks.append(check("infra", "git_remote", "pass" if remotes else "fail", f"Remotes: {remotes or 'none (no off-machine backup)'}"))

    tracked_env = []
    if is_git:
        code, tracked = git(root, "ls-files", "--", ".env", ".env.*", "**/.env", "**/.env.*")
        if code != 0:
            raise RuntimeError(f"Unable to check tracked environment files: {tracked}")
        tracked_env = [name for name in tracked.splitlines()
                       if not re.search(r"\.(example|sample|template|dist)$", name)]
    if tracked_env:
        checks.append(check("infra", "env_committed", "fail", "Env files tracked by git", files=tracked_env))
    else:
        checks.append(check("infra", "env_committed", "manual", "Confirm environment files are untracked and correctly ignored, including nested files."))
    checks.append(check("security", "env_contents", "manual",
                        "Environment files are excluded from scanning. Ask the user to check their contents and credential handling privately; never share values."))

    checks.append(check("infra", "ci", "pass" if (root / ".github" / "workflows").is_dir() else "warn", "CI workflows " + ("found" if (root / ".github" / "workflows").is_dir() else "not found")))
    for cid, q in (("staging", "Is there a staging environment before production?"),
                   ("hosting_defaults", "Explain the chosen hosting model's cold-start, availability, recovery and cost tradeoffs against the agreed requirements."),
                   ("backups", "Are database backups stored outside the volume and account the app and agent can reach? Has a restore been done once?"),
                   ("agent_permissions", "What can the AI agent read, write and delete?")):
        checks.append(check("infra", cid, "manual", q))

    # Names and config files the app uses, for the per-service rows below
    names = set()
    for p in files:
        if p.name.endswith(CODE_EXTS):
            names |= set(ENV_NAME_RE.findall(read(p)))
    dep_text = " ".join(read(root / d).lower() for d in DEP_FILES)

    # Pillar 2: code quality and testing
    tests = [rel(p) for p in files if re.search(r"(^test_|\.test\.|\.spec\.)", p.name) or "/tests/" in "/" + rel(p)]
    checks.append(check("quality", "tests_exist", "pass" if tests else "fail", f"{len(tests)} test file(s)", sample=tests[:5]))
    checks.append(check("quality", "critical_flow_covered", "manual", "Does at least one test cover the critical user flow?"))

    # Pillar 3: security and data
    secrets = scan_secrets(root, files)
    checks.append(check("security", "secrets_in_source", "warn" if secrets else "manual", f"{len(secrets)} file(s) with possible secrets; confirm privately without exposing values" if secrets else "No patterns matched; secret safety remains unverified", hits=secrets[:20]))
    flagged = scan_endpoints(root, files)
    checks.append(check("security", "endpoints_without_auth", "warn" if flagged else "manual",
                        "Heuristic: these route files mention no auth; review each and verify all protected routes and intentional public paths." if flagged else "No route files flagged; verify all protected routes and intentional public paths.", files=flagged[:30]))
    uses_supabase = any("supabase" in read(p).lower() for p in files if p.name in DEP_FILES) or (root / "supabase").is_dir()
    if uses_supabase:
        n, gaps = rls_gaps(files)
        if n == 0:
            checks.append(check("security", "rls", "manual", "Supabase in use but no CREATE TABLE in SQL files. Check RLS in the dashboard."))
        else:
            checks.append(check("security", "rls", "warn" if gaps else "manual", f"{len(gaps)} of {n} detected table(s) lack an RLS enable statement; verify access controls" if gaps else f"RLS enable statements found for {n} detected table(s); verify policies and access", tables=gaps))
    lock = [l for l in LOCKFILES if (root / l).exists()]
    has_deps = any((root / d).exists() for d in DEP_FILES)
    if has_deps:
        checks.append(check("security", "lockfile", "pass" if lock else "warn", f"Lockfile: {lock[0]}" if lock else "No lockfile; installs are not reproducible"))
        checks.append(check("security", "dependency_audit", "manual", "Run `npm audit` / `pip-audit` and review what the AI pulled in."))
    checks.append(check("security", "ai_data_handling", "manual", "What customer data reaches third-party AI tools?"))

    paths = {rel(p) for p in files}
    hosts = [h for h, (configs, envs) in INFRA_HOSTS.items()
             if any(c in paths for c in configs) or names & set(envs) or (h == "Terraform" and any(p.endswith(".tf") for p in paths))]
    for h in hosts:
        checks.append(check("security", f"infra_token:{h}", "manual",
                            f"{h} tokens: each scoped to one environment and only the actions it needs? Production tokens only in the host's dashboard, never in the repo, CI logs or the agent's environment?"))
    if not hosts:
        checks.append(check("security", "infra_tokens", "manual",
                            "Which deploy and cloud tokens exist? Each scoped to one environment and only the actions it needs? Production tokens only in the host's dashboard?"))

    ci_text = " ".join(read(p) for p in files if rel(p).startswith(".github/workflows/") or rel(p) in CI_FILES)
    if not ci_text:
        checks.append(check("security", "ci_secret_scan", "warn", "No CI, so nothing scans for secrets on every push"))
    else:
        scanning = bool(SECRET_SCANNERS.search(ci_text))
        checks.append(check("security", "ci_secret_scan", "manual" if scanning else "warn",
                            "Possible secret scanner reference found; verify it actually runs and covers changes" if scanning else "No secret scanner reference found; verify CI configuration"))

    # Pillar 3 (continued): runtime locks, only when the app calls a model
    deps = dep_text
    if any(sdk in deps for sdk in AI_SDKS):
        powerful = []
        for p in files:
            if p.suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs"):
                text = read(p)
                if TOOL_USE_RE.search(text) and POWER_RE.search(text):
                    powerful.append(rel(p))
        checks.append(check("security", "ai_tool_review", "warn" if powerful else "manual",
                            "Heuristic: these files define model tools and mention a delete, send, exec, charge or publish capability. Confirm each tool is needed and least-privilege." if powerful
                            else "No model tool definition found with a powerful capability", files=powerful[:30]))
        has_validation = [v for v in VALIDATION_LIBS if v in deps]
        checks.append(check("security", "ai_validation", "manual" if has_validation else "warn",
                            f"Schema library present: {', '.join(has_validation)}. Confirm tool arguments go through it." if has_validation
                            else "No schema validation library; tool arguments may be passed through unchecked"))
        for cid, q in (("ai_approval", "Do irreversible actions (send, delete, pay, publish) need approval bound to the exact action?"),
                       ("ai_pii_redaction", "Is personal data minimized and are identifiers redacted unless necessary? Before necessary identifying data is sent, is the data flow approved and are applicable privacy, security, provider terms and required reviews verified?"),
                       ("ai_untrusted_text", "Is retrieved or uploaded text labeled untrusted? Does any feature combine private data, untrusted content and a way to send data out?")):
            checks.append(check("security", cid, "manual", q))

    # Pillars 4 and 3: observability, cost, rate limits
    tracker = [t for t in ERROR_TRACKERS if t in dep_text]
    checks.append(check("observability", "error_tracker", "manual" if tracker else "warn", f"Possible error tracker: {', '.join(tracker)}; verify detection and investigation" if tracker else "No recognized error tracker; verify another effective error detection and investigation mechanism"))
    limiter = [r for r in RATE_LIMITERS if r in dep_text]
    checks.append(check("infra", "rate_limit", "manual" if limiter else "warn", f"Possible rate limiter: {', '.join(limiter)}; verify coverage and enforcement" if limiter else "No recognized rate-limit dependency; verify application and host controls"))
    paid = [s for s, (pkgs, envs) in PAID_SERVICES.items() if any(p in dep_text for p in pkgs) or names & set(envs)]
    for s in paid:
        checks.append(check("observability", f"paid_key:{s}", "manual",
                            f"{s} key: verify a provider-enforced hard cap, spend alerts and restricted scope. If unavailable, assess limits in your own code and residual risk from direct key use, concurrency and delayed billing."))
    checks.append(check("observability", "monthly_cost", "manual", "Add up hosting, database and API spend." +
                        ("" if paid else " Any paid API: spend cap, spend alerts, key restricted to the APIs it uses?")))

    # Pillar 5: failure and rollback
    checks.append(check("rollback", "rollback_dry_run", "manual", "Has anyone done a rollback dry run?"))
    checks.append(check("rollback", "runbook", "manual", "Is there a runbook: who to call, what to check first, what to do on a data breach?"))

    counts = {s: sum(c["status"] == s for c in checks) for s in ("pass", "warn", "fail", "manual")}
    print(json.dumps({"root": str(root), "counts": counts, "checks": checks}, indent=2))
    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
