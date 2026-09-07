import ast
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
    def test_builder_exposes_all_46_actions(self):
        actions = python_action_set(ROOT / "scripts/build_ds_webhook_payload.py")
        self.assertEqual(46, len(actions))
        self.assertTrue({
            "resolve_project",
            "check_failed_instances",
            "find_resource_usage",
            "search_country_git_sql",
            "stop_instance",
            "force_fail_instance",
            "list_alert_groups",
            "batch_update_schedule_alerts",
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


if __name__ == "__main__":
    unittest.main()
