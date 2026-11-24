"""Stdlib tests for audit_repo.py. Run: python3 -m unittest discover -s product-launch-audit/tests"""

import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

AUDIT = Path(__file__).resolve().parent.parent / "scripts" / "audit_repo.py"
SPEC = importlib.util.spec_from_file_location("launch_audit", AUDIT)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class AuditCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def checks(self):
        r = subprocess.run([sys.executable, AUDIT, self.root], capture_output=True, text=True)
        return {c["id"]: c for c in json.loads(r.stdout)["checks"]}


class PaidKeyTests(AuditCase):
    def test_one_spend_row_per_paid_service(self):
        self.write("requirements.txt", "openai==1.0\nfastapi\n")
        self.write("config.example.txt", "GEMINI_API_KEY=\nELEVENLABS_API_KEY=\n")
        checks = self.checks()
        for service in ("OpenAI", "Google Gemini", "ElevenLabs"):
            with self.subTest(service=service):
                row = checks[f"paid_key:{service}"]
                self.assertEqual(row["status"], "manual")
                self.assertEqual(row["pillar"], "observability")
                for word in ("cap", "alert", "restricted", "your own code"):
                    self.assertIn(word, row["detail"])
        self.assertNotIn("paid_key:Anthropic", checks)

    def test_no_paid_services_keeps_generic_cost_row(self):
        self.write("package.json", '{"dependencies": {"express": "4"}}')
        checks = self.checks()
        self.assertFalse([c for c in checks if c.startswith("paid_key:")])
        self.assertEqual(checks["monthly_cost"]["status"], "manual")


class InfraTokenTests(AuditCase):
    def test_one_scope_row_per_host(self):
        self.write("railway.json", "{}")
        self.write("render.yaml", "services: []\n")
        self.write("infra/main.tf", 'provider "aws" {}\n')
        checks = self.checks()
        for host in ("Railway", "Render", "Terraform"):
            with self.subTest(host=host):
                row = checks[f"infra_token:{host}"]
                self.assertEqual((row["status"], row["pillar"]), ("manual", "security"))
                self.assertIn("one environment", row["detail"])

    def test_host_found_from_env_var_name(self):
        self.write("scripts/deploy.sh", 'railway up --service "$SERVICE"  # needs RAILWAY_TOKEN\n')
        self.assertIn("infra_token:Railway", self.checks())

    def test_no_host_asks_generically(self):
        self.assertEqual(self.checks()["infra_tokens"]["status"], "manual")


class BackupTests(AuditCase):
    def test_backups_row_asks_off_volume_and_restore(self):
        row = self.checks()["backups"]
        self.assertEqual((row["status"], row["pillar"]), ("manual", "infra"))
        self.assertIn("outside", row["detail"])
        self.assertIn("restore", row["detail"])


class CiSecretScanTests(AuditCase):
    def test_no_ci_warns(self):
        self.assertEqual(self.checks()["ci_secret_scan"]["status"], "warn")

    def test_ci_without_scanner_warns(self):
        self.write(".github/workflows/test.yml", "jobs:\n  test:\n    steps:\n      - run: pytest\n")
        self.assertEqual(self.checks()["ci_secret_scan"]["status"], "warn")

    def test_ci_with_scanner_needs_verification(self):
        for step in ("uses: gitleaks/gitleaks-action@v2", "run: python3 check_loop.py guardrails", "run: trufflehog git file://."):
            with self.subTest(step=step):
                self.write(".github/workflows/test.yml", f"jobs:\n  scan:\n    steps:\n      - {step}\n")
                self.assertEqual(self.checks()["ci_secret_scan"]["status"], "manual")


class ProtectedFileTests(unittest.TestCase):
    def test_skips_sensitive_paths_before_reading(self):
        root = Path("/synthetic")
        entries = [
            (str(root), ["secrets", "src"], [".env", ".env.example", ".env.local", "cert.pem", "secret.key", "app.py"]),
            (str(root / "src"), [], [".env.production", "route.ts"]),
        ]
        with patch.object(audit.os, "walk", return_value=iter(entries)):
            files = audit.list_files(root)
        self.assertEqual(files, [root / "app.py", root / "src" / "route.ts"])
        self.assertNotIn("secrets", entries[0][1])
        for path in (root / ".env", root / "src" / ".env.production", root / "secrets" / "file.txt", root / "cert.pem", root / ".agent" / "guardrails.json"):
            with self.subTest(path=path), patch.object(Path, "read_text", side_effect=AssertionError("must not read")):
                self.assertRaises(ValueError, audit.read, path)

    def test_env_review_is_explicit(self):
        with tempfile.TemporaryDirectory() as root:
            result = subprocess.run([sys.executable, AUDIT, root], capture_output=True, text=True)
            checks = {c["id"]: c for c in json.loads(result.stdout)["checks"]}
        self.assertEqual(checks["env_contents"]["status"], "manual")
        self.assertIn("user", checks["env_contents"]["detail"].lower())


class HeuristicTests(AuditCase):
    def test_ai_data_check_requires_minimization_and_verified_conditions(self):
        self.write("package.json", '{"dependencies":{"openai":"1"}}')
        row = self.checks()["ai_pii_redaction"]
        self.assertEqual(row["status"], "manual")
        for phrase in ("minimized", "redacted", "necessary", "approved", "verified"):
            self.assertIn(phrase, row["detail"].lower())

    def test_heuristics_do_not_claim_security_controls_pass(self):
        self.write("package.json", '{"dependencies":{"openai":"1", "zod":"1", "sentry":"1", "express-rate-limit":"1"}}')
        self.write("app.ts", "app.get('/private', () => {}) // auth\n")
        checks = self.checks()
        for key in ("endpoints_without_auth", "secrets_in_source", "ai_tool_review", "ai_validation", "rate_limit", "error_tracker"):
            with self.subTest(key=key):
                self.assertNotEqual(checks[key]["status"], "pass")

    def test_absent_error_tracker_is_warning_not_failure(self):
        self.assertEqual(self.checks()["error_tracker"]["status"], "warn")

    def test_rls_enable_statement_is_not_a_verified_policy(self):
        self.write("package.json", '{"dependencies":{"@supabase/supabase-js":"1"}}')
        self.write("schema.sql", "CREATE TABLE profiles (id text); ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;")
        self.assertEqual(self.checks()["rls"]["status"], "manual")

    def test_no_secret_pattern_match_is_not_a_security_pass(self):
        self.write("app.ts", "const value = 'safe placeholder';")
        self.assertEqual(self.checks()["secrets_in_source"]["status"], "manual")

    def test_cloudflare_jsonc_is_recognized(self):
        self.write("wrangler.jsonc", "{}")
        self.assertEqual(self.checks()["infra_token:Cloudflare"]["status"], "manual")


if __name__ == "__main__":
    unittest.main()
