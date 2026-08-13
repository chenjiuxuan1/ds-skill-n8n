import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_ds_webhook_payload.py"
NORMALIZER = ROOT / "n8n/request_normalizer.js"


def run_builder(*args):
    command = [
        sys.executable,
        str(BUILDER),
        "--webhook-url",
        "https://example.invalid/webhook/ds-scheduler",
        "--country",
        "ph",
        "--ds-token",
        "test-secret-token",
        *args,
    ]
    return subprocess.run(command, text=True, capture_output=True, check=False)


def parse_payload(stdout):
    value, _ = json.JSONDecoder().raw_decode(stdout)
    return value


class BuilderScheduleAlertTests(unittest.TestCase):
    def test_builds_alert_group_lookup(self):
        completed = run_builder(
            "--action",
            "list_alert_groups",
            "--search-val",
            "n8n告警触发器",
            "--page-no",
            "2",
            "--page-size",
            "100",
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = parse_payload(completed.stdout)["payload"]
        self.assertEqual("n8n告警触发器", payload["search_val"])
        self.assertEqual(2, payload["page_no"])
        self.assertEqual(100, payload["page_size"])

    def test_builds_safe_batch_dry_run_by_default(self):
        completed = run_builder(
            "--action",
            "batch_update_schedule_alerts",
            "--project-names-json",
            '["DW_DWB","DW_DWD"]',
            "--workflow-release-state",
            "ONLINE",
            "--schedule-release-state",
            "ONLINE",
            "--warning-type",
            "failure",
            "--warning-group-name",
            "n8n告警触发器",
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = parse_payload(completed.stdout)["payload"]
        self.assertEqual(["DW_DWB", "DW_DWD"], payload["project_names"])
        self.assertEqual("ONLINE", payload["workflow_release_state"])
        self.assertEqual("ONLINE", payload["schedule_release_state"])
        self.assertEqual("FAILURE", payload["warning_type"])
        self.assertEqual("n8n告警触发器", payload["warning_group_name"])
        self.assertIs(payload["dry_run"], True)

    def test_execute_flag_is_required_to_disable_dry_run(self):
        completed = run_builder(
            "--action",
            "batch_update_schedule_alerts",
            "--project-names-json",
            '["DW_DWB"]',
            "--workflow-release-state",
            "ONLINE",
            "--schedule-release-state",
            "ONLINE",
            "--warning-type",
            "FAILURE",
            "--warning-group-name",
            "n8n告警触发器",
            "--execute",
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIs(parse_payload(completed.stdout)["payload"]["dry_run"], False)

    def test_update_schedule_accepts_alert_fields_without_crontab(self):
        completed = run_builder(
            "--action",
            "update_schedule",
            "--project-code",
            "100",
            "--schedule-id",
            "501",
            "--warning-type",
            "FAILURE",
            "--warning-group-id",
            "42",
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = parse_payload(completed.stdout)["payload"]
        self.assertEqual("FAILURE", payload["warning_type"])
        self.assertEqual("42", payload["warning_group_id"])

    def test_invalid_warning_type_does_not_echo_token_in_error(self):
        completed = run_builder(
            "--action",
            "update_schedule",
            "--project-code",
            "100",
            "--schedule-id",
            "501",
            "--warning-type",
            "INVALID",
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertNotIn("test-secret-token", completed.stderr)


class NormalizerScheduleAlertTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = NORMALIZER.read_text(encoding="utf-8")

    def test_normalizes_batch_fields_without_token_in_payload(self):
        for field in (
            "project_names",
            "workflow_release_state",
            "schedule_release_state",
            "warning_group_name",
            "dry_run",
            "retry_attempts",
            "retry_delay_ms",
            "rate_limit_ms",
        ):
            self.assertIn(field, self.text)
        self.assertNotRegex(self.text, r"payload\.ds_token\s*=")

    def test_validates_batch_and_warning_type(self):
        self.assertIn("batch_update_schedule_alerts requires project_names", self.text)
        self.assertIn("warning_type must be one of NONE, SUCCESS, FAILURE, ALL", self.text)
        self.assertIn("dry_run must be a boolean", self.text)


if __name__ == "__main__":
    unittest.main()
