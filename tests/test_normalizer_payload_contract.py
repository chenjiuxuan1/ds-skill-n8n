"""Contract tests for the n8n request normalizer's boolean-flag handling.

The normalizer is the only gate between a caller and the gateway, and it has an
explicit payload allowlist. A flag that is silently *dropped* for being the
wrong type is worse than one that is rejected: the caller believes the option
was honoured while the gateway quietly applies its default.

These tests run the real ``request_normalizer.js`` under node and assert both
directions: good values survive into the base64 payload, bad values are
reported as errors instead of vanishing.

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

HARNESS = """
const { readFileSync } = require('node:fs');
const src = readFileSync(process.argv[2], 'utf8');
const cases = JSON.parse(readFileSync(process.argv[3], 'utf8'));
const factory = new Function('$json', src);
const out = {};
for (const name of Object.keys(cases)) {
  const result = factory({ body: cases[name] })[0].json;
  out[name] = {
    valid: result.valid,
    errors: result.errors,
    payload_b64: result.payload_b64,
  };
}
process.stdout.write(JSON.stringify(out));
"""

FLAGS = ("restore_original_state", "auto_offline", "include_schedule", "require_global_params")


def request(action, payload):
    return {
        "source": "codex-skill",
        "country": "mx",
        "action": action,
        "ds_token": "T",
        "request_id": "test-1",
        "payload": payload,
    }


SINGLE = {"project_code": "1", "workflow_code": "2", "environment_code": "123"}
BATCH = {"project_code": "1", "workflow_codes": ["2", "3"], "environment_code": "123"}
TASK = {"project_code": "1", "workflow_code": "2", "task_name": "t1"}


@unittest.skipUnless(NODE, "node is required to exercise the n8n normalizer")
class NormalizerFlagContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cases = {
            # ---- accepted, and the value must survive into the payload ----
            "ok_single_default": request("update_workflow_environment", SINGLE),
            "ok_single_execute": request(
                "update_workflow_environment", {**SINGLE, "dry_run": False}
            ),
            "ok_single_schedule": request(
                "update_workflow_environment",
                {**SINGLE, "include_schedule": True, "require_global_params": True},
            ),
            "ok_single_all_flags": request(
                "update_workflow_environment",
                {
                    **SINGLE,
                    "include_schedule": False,
                    "require_global_params": False,
                    "restore_original_state": False,
                    "auto_offline": False,
                },
            ),
            "ok_batch": request("batch_update_workflow_environment", BATCH),
            "ok_batch_scalar": request(
                "batch_update_workflow_environment",
                {"project_code": "1", "workflow_codes": "2", "environment_code": "123"},
            ),
            # ---- task retry settings ----
            "ok_retry_times": request("update_task", {**TASK, "fail_retry_times": 3}),
            "ok_retry_both": request(
                "update_task", {**TASK, "fail_retry_times": 3, "fail_retry_interval": 5}
            ),
            "ok_retry_zero": request("update_task", {**TASK, "fail_retry_times": 0}),
            "ok_retry_numeric_string": request("update_task", {**TASK, "fail_retry_times": "4"}),
            "ok_retry_absent": request("update_task", dict(TASK)),
            "bad_retry_string": request("update_task", {**TASK, "fail_retry_times": "abc"}),
            "bad_retry_bool": request("update_task", {**TASK, "fail_retry_times": True}),
            "bad_retry_negative": request("update_task", {**TASK, "fail_retry_times": -1}),
            "bad_retry_float": request("update_task", {**TASK, "fail_retry_times": 1.5}),
            "bad_retry_too_big": request(
                "update_task", {**TASK, "fail_retry_interval": 99999}
            ),
            # ---- rejected: a wrong-typed flag must not be silently dropped ----
            "bad_dry_run": request(
                "update_workflow_environment", {**SINGLE, "dry_run": "false"}
            ),
            "bad_include_schedule": request(
                "update_workflow_environment", {**SINGLE, "include_schedule": "yes"}
            ),
            "bad_require_global_params": request(
                "update_workflow_environment", {**SINGLE, "require_global_params": "true"}
            ),
            "bad_restore_original_state": request(
                "update_workflow_environment", {**SINGLE, "restore_original_state": 0}
            ),
            "bad_auto_offline": request(
                "update_workflow_environment", {**SINGLE, "auto_offline": "no"}
            ),
            "batch_bad_include_schedule": request(
                "batch_update_workflow_environment", {**BATCH, "include_schedule": "yes"}
            ),
            "batch_bad_auto_offline": request(
                "batch_update_workflow_environment", {**BATCH, "auto_offline": "no"}
            ),
            "batch_no_codes": request(
                "batch_update_workflow_environment",
                {"project_code": "1", "workflow_codes": [], "environment_code": "123"},
            ),
            "batch_duplicate_codes": request(
                "batch_update_workflow_environment",
                {"project_code": "1", "workflow_codes": ["2", "2"], "environment_code": "123"},
            ),
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

    def decoded(self, name):
        payload = self.results[name]["payload_b64"]
        return json.loads(base64.b64decode(payload).decode("utf-8"))

    def assertRejected(self, name, expected_error):
        result = self.results[name]
        self.assertFalse(result["valid"], f"{name} should have been rejected")
        self.assertIn(expected_error, result["errors"])

    def test_valid_requests_are_accepted(self):
        for name in (
            "ok_single_default",
            "ok_single_execute",
            "ok_single_schedule",
            "ok_single_all_flags",
            "ok_batch",
            "ok_batch_scalar",
            "ok_retry_times",
            "ok_retry_both",
            "ok_retry_zero",
            "ok_retry_numeric_string",
            "ok_retry_absent",
        ):
            with self.subTest(name=name):
                self.assertTrue(self.results[name]["valid"], self.results[name]["errors"])
                self.assertEqual([], self.results[name]["errors"])

    def test_dry_run_defaults_to_true_and_is_preserved(self):
        self.assertIs(True, self.decoded("ok_single_default")["dry_run"])
        self.assertIs(False, self.decoded("ok_single_execute")["dry_run"])

    def test_explicit_booleans_survive_into_the_payload(self):
        payload = self.decoded("ok_single_schedule")
        self.assertIs(True, payload["include_schedule"])
        self.assertIs(True, payload["require_global_params"])
        explicit = self.decoded("ok_single_all_flags")
        for flag in FLAGS:
            with self.subTest(flag=flag):
                self.assertIs(False, explicit[flag])

    def test_absent_flags_serialize_away_so_gateway_defaults_apply(self):
        payload = self.decoded("ok_single_default")
        for flag in FLAGS:
            with self.subTest(flag=flag):
                self.assertNotIn(flag, payload)

    def test_wrong_typed_flags_are_rejected_not_dropped(self):
        for flag in FLAGS:
            with self.subTest(flag=flag):
                self.assertRejected(f"bad_{flag}", f"{flag} must be a boolean")

    def test_batch_codes_are_normalized(self):
        self.assertEqual(["2", "3"], self.decoded("ok_batch")["workflow_codes"])
        self.assertEqual(["2"], self.decoded("ok_batch_scalar")["workflow_codes"])

    def test_batch_rejects_bad_code_lists(self):
        self.assertRejected(
            "batch_no_codes", "batch_update_workflow_environment requires workflow_codes"
        )
        self.assertRejected(
            "batch_duplicate_codes", "workflow_codes must contain unique non-empty strings"
        )

    def test_batch_rejects_wrong_typed_flags(self):
        self.assertRejected("batch_bad_include_schedule", "include_schedule must be a boolean")
        self.assertRejected("batch_bad_auto_offline", "auto_offline must be a boolean")

    def test_task_retry_values_survive_into_the_payload(self):
        self.assertEqual(3, self.decoded("ok_retry_times")["fail_retry_times"])
        both = self.decoded("ok_retry_both")
        self.assertEqual(3, both["fail_retry_times"])
        self.assertEqual(5, both["fail_retry_interval"])
        self.assertEqual(4, self.decoded("ok_retry_numeric_string")["fail_retry_times"])

    def test_zero_retries_is_kept_not_treated_as_absent(self):
        """0 clears retries; it must not be collapsed into 'field missing'."""
        payload = self.decoded("ok_retry_zero")
        self.assertIn("fail_retry_times", payload)
        self.assertEqual(0, payload["fail_retry_times"])

    def test_absent_retry_settings_serialize_away(self):
        payload = self.decoded("ok_retry_absent")
        self.assertNotIn("fail_retry_times", payload)
        self.assertNotIn("fail_retry_interval", payload)

    def test_wrong_typed_retry_settings_are_rejected_not_dropped(self):
        self.assertRejected("bad_retry_string", "fail_retry_times must be an integer")
        self.assertRejected("bad_retry_bool", "fail_retry_times must be an integer")
        self.assertRejected("bad_retry_float", "fail_retry_times must be an integer")
        self.assertRejected(
            "bad_retry_negative", "fail_retry_times must be between 0 and 1000"
        )
        self.assertRejected(
            "bad_retry_too_big", "fail_retry_interval must be between 0 and 10080"
        )


if __name__ == "__main__":
    unittest.main()
