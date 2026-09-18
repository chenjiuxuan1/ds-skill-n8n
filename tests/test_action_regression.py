"""Regression guard: the new features must not touch the other actions.

The normalizer is a single shared script with a 48-action allowlist and a large
payload allowlist. Adding task-level retry handling to it must be provably
inert for every other action, and every action must keep returning the same
output contract.

The strongest formulation of "no side effect" needs no per-action valid
payload: for each action, the normalizer is run twice on the *same* body, once
with the retry fields injected and once without, and the two results must be
identical for every action outside the update family. Any leak out of the
retry block shows up immediately.

Skipped when node is not installed.
"""

import base64
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NORMALIZER = ROOT / "n8n/request_normalizer.js"
NODE = shutil.which("node")

RETRY_FIELDS = ("fail_retry_times", "fail_retry_interval")
UPDATE_FAMILY = ("update_task", "update_sql_task", "update_shell_task")

HARNESS = """
const { readFileSync } = require('node:fs');
const src = readFileSync(process.argv[2], 'utf8');
const cases = JSON.parse(readFileSync(process.argv[3], 'utf8'));
const factory = new Function('$json', src);
const out = {};
for (const name of Object.keys(cases)) {
  const result = factory({ body: cases[name] })[0].json;
  out[name] = {
    action: result.action,
    country: result.country,
    valid: result.valid,
    errors: result.errors,
    payload: JSON.parse(result.payload_json),
    payload_b64: result.payload_b64,
    payload_json: result.payload_json,
  };
}
process.stdout.write(JSON.stringify(out));
"""


def actions(code):
    import re

    body = re.search(r"const ACTIONS = new Set\(\[(.*?)\]\);", code, re.S).group(1)
    return sorted(set(re.findall(r"'([^']+)'", body)))


def base_payload():
    """A generic body: it does not need to be valid for every action, only
    identical between the two runs of the same action."""
    return {
        "project_code": "158514956085248",
        "project_name": "",
        "workflow_code": "174599383687393",
        "workflow_name": "",
        "workflow_codes": ["174599383687393"],
        "task_name": "shell_task",
        "task_code": "9001",
        "environment_code": "12813621425120",
        "instance_id": "1",
        "sql": "select 1",
        "script": "echo 1",
        "crontab": "0 0 3 * * ? *",
        "resource_type": "FILE",
        "full_name": "/data/x.sql",
    }


@unittest.skipUnless(NODE, "node is required to exercise the n8n normalizer")
class AllActionRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        code = NORMALIZER.read_text(encoding="utf-8")
        cls.actions = actions(code)
        cases = {}
        for action in cls.actions:
            body = {
                "source": "codex-skill",
                "country": "mx",
                "action": action,
                "ds_token": "T",
                "request_id": "regression-1",
                "payload": base_payload(),
            }
            cases[f"{action}::plain"] = body
            cases[f"{action}::retry"] = {
                **body,
                "payload": {**base_payload(), "fail_retry_times": 3, "fail_retry_interval": 5},
            }
            cases[f"{action}::badretry"] = {
                **body,
                "payload": {**base_payload(), "fail_retry_times": "not-an-int"},
            }

        with tempfile.TemporaryDirectory() as tmp:
            harness = Path(tmp) / "harness.js"
            harness.write_text(HARNESS, encoding="utf-8")
            cases_path = Path(tmp) / "cases.json"
            cases_path.write_text(json.dumps(cases), encoding="utf-8")
            proc = subprocess.run(
                [NODE, str(harness), str(NORMALIZER), str(cases_path)],
                capture_output=True,
                text=True,
            )
        if proc.returncode != 0:
            raise AssertionError(f"normalizer harness failed: {proc.stderr}")
        cls.results = json.loads(proc.stdout)

    def get(self, action, suffix):
        return self.results[f"{action}::{suffix}"]

    # ---- the action surface is unchanged -----------------------------------

    def test_the_action_surface_is_still_48(self):
        self.assertEqual(48, len(self.actions))

    def test_update_family_is_present_in_the_allowlist(self):
        for action in UPDATE_FAMILY:
            self.assertIn(action, self.actions)

    # ---- every action keeps its output contract ---------------------------

    def test_every_action_still_returns_the_expected_contract(self):
        for action in self.actions:
            for suffix in ("plain", "retry", "badretry"):
                with self.subTest(action=action, variant=suffix):
                    result = self.get(action, suffix)
                    self.assertEqual(action, result["action"])
                    self.assertEqual("mx", result["country"])
                    self.assertIsInstance(result["valid"], bool)
                    self.assertIsInstance(result["errors"], list)
                    self.assertIsInstance(result["payload"], dict)
                    # payload_json / payload_b64 must agree with each other
                    self.assertEqual(result["payload"], json.loads(result["payload_json"]))
                    self.assertEqual(
                        result["payload"],
                        json.loads(base64.b64decode(result["payload_b64"]).decode("utf-8")),
                    )

    # ---- the retry fields are inert for every other action ----------------

    def test_retry_fields_do_not_change_any_other_action(self):
        others = [a for a in self.actions if a not in UPDATE_FAMILY]
        self.assertEqual(45, len(others))
        for action in others:
            plain, retry = self.get(action, "plain"), self.get(action, "retry")
            with self.subTest(action=action):
                self.assertEqual(plain["payload"], retry["payload"],
                                 f"{action}: retry fields leaked into the payload")
                self.assertEqual(plain["valid"], retry["valid"])
                self.assertEqual(plain["errors"], retry["errors"])

    def test_bad_retry_values_do_not_invalidate_any_other_action(self):
        for action in (a for a in self.actions if a not in UPDATE_FAMILY):
            plain, bad = self.get(action, "plain"), self.get(action, "badretry")
            with self.subTest(action=action):
                self.assertEqual(plain["valid"], bad["valid"],
                                 f"{action}: an ignored field changed validity")
                self.assertEqual(plain["errors"], bad["errors"])
                self.assertNotIn("fail_retry_times", bad["payload"])

    def test_retry_fields_are_absent_from_other_actions_by_default(self):
        for action in (a for a in self.actions if a not in UPDATE_FAMILY):
            with self.subTest(action=action):
                payload = self.get(action, "plain")["payload"]
                for field in RETRY_FIELDS:
                    self.assertNotIn(field, payload)

    # ---- and they do work for the update family ---------------------------

    def test_update_family_receives_the_validated_values(self):
        for action in UPDATE_FAMILY:
            with self.subTest(action=action):
                payload = self.get(action, "retry")["payload"]
                self.assertEqual(3, payload["fail_retry_times"])
                self.assertEqual(5, payload["fail_retry_interval"])

    def test_update_family_rejects_a_bad_value(self):
        for action in UPDATE_FAMILY:
            with self.subTest(action=action):
                result = self.get(action, "badretry")
                self.assertFalse(result["valid"])
                self.assertIn("fail_retry_times must be an integer", result["errors"])

    def test_update_family_is_unaffected_when_the_fields_are_absent(self):
        for action in UPDATE_FAMILY:
            with self.subTest(action=action):
                plain = self.get(action, "plain")
                for field in RETRY_FIELDS:
                    self.assertNotIn(field, plain["payload"])


if __name__ == "__main__":
    unittest.main()
