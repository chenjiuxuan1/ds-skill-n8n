import ast
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def python_action_set(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "ACTIONS" for target in node.targets)
        ):
            return {item.value for item in node.value.elts}
    raise AssertionError("ACTIONS not found")


class ActionAlignmentTests(unittest.TestCase):
    def test_builder_exposes_the_full_action_set(self):
        actions = python_action_set(ROOT / "scripts/build_ds_webhook_payload.py")
        self.assertEqual(48, len(actions))
        self.assertTrue({
            "resolve_project",
            "check_failed_instances",
            "find_resource_usage",
            "search_country_git_sql",
            "stop_instance",
            "force_fail_instance",
            "list_alert_groups",
            "batch_update_schedule_alerts",
            "update_workflow_environment",
            "batch_update_workflow_environment",
            "get_auto_repair_log",
            "copy_workflow",
            "get_alert_instance",
        }.issubset(actions))

    def test_normalizer_exposes_same_actions(self):
        text = (ROOT / "n8n/request_normalizer.js").read_text(encoding="utf-8")
        body = re.search(r"const ACTIONS = new Set\(\[(.*?)\]\);", text, re.S).group(1)
        js_actions = set(re.findall(r"'([^']+)'", body))
        self.assertEqual(
            python_action_set(ROOT / "scripts/build_ds_webhook_payload.py"),
            js_actions,
        )

    def test_shell_handled_actions_are_declared_as_such(self):
        """Some allowlisted actions never reach the gateway.

        ``find_resource_usage`` and ``get_auto_repair_log`` are executed by the
        remote shell block of each country node, so they are deliberately absent
        from the gateway's ``SUPPORTED_ACTIONS``. Without this list it looks like
        the two artifacts disagree; with it, the router must actually implement
        the intercept.
        """
        shell_only = {"find_resource_usage", "get_auto_repair_log"}
        actions = python_action_set(ROOT / "scripts/build_ds_webhook_payload.py")
        self.assertTrue(shell_only.issubset(actions))

        wf = json.loads((ROOT / "n8n/ds-scheduler-router.latest.json").read_text(encoding="utf-8"))
        country_nodes = [n for n in wf["nodes"] if n["name"] in
                         {"中国", "菲律宾", "印尼", "墨西哥", "泰国", "巴基斯坦"}]
        self.assertEqual(6, len(country_nodes))
        for node in country_nodes:
            command = node["parameters"]["command"]
            for action in shell_only:
                with self.subTest(node=node["name"], action=action):
                    self.assertIn(
                        f'[ "$ACTION" = "{action}" ]',
                        command,
                        f"{node['name']} does not intercept {action}",
                    )
            # a trailing else branch must still forward everything else to the gateway
            self.assertIn("ds_scheduler_entry.py", command)


if __name__ == "__main__":
    unittest.main()
