import hashlib
import json
import re
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NORMALIZER = ROOT / "n8n/request_normalizer.js"
ARTIFACTS = {
    ROOT / "n8n/workflow-template.json": {
        "nodes": 21,
        "connections": 17,
        "structural_hash": "771bff09f36e5d8bf57cf38d7ac6d5c0043e8e463c3ab6ebc2cd6e4090a66ee5",
    },
    ROOT / "n8n/ds-scheduler-router.latest.json": {
        "nodes": 24,
        "connections": 19,
        "structural_hash": "49ebedf634bb48e6814e1be48a5c7ac7b7d963edd405340e9c84ac2e470d3798",
    },
}


def normalizer_node(workflow):
    nodes = [node for node in workflow["nodes"] if node["name"] == "解析并标准化请求"]
    if len(nodes) != 1:
        raise AssertionError("expected exactly one request normalizer node")
    return nodes[0]


def structural_hash(workflow):
    sanitized = deepcopy(workflow)
    normalizer_node(sanitized)["parameters"]["jsCode"] = "<NORMALIZER>"
    raw = json.dumps(
        sanitized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def actions(code):
    body = re.search(r"const ACTIONS = new Set\(\[(.*?)\]\);", code, re.S).group(1)
    return set(re.findall(r"'([^']+)'", body))


class RouterArtifactTests(unittest.TestCase):
    def test_artifacts_embed_the_checked_in_normalizer_only(self):
        expected_code = NORMALIZER.read_text(encoding="utf-8")
        for path, expected in ARTIFACTS.items():
            with self.subTest(path=path.name):
                workflow = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(expected["nodes"], len(workflow["nodes"]))
                self.assertEqual(expected["connections"], len(workflow["connections"]))
                self.assertEqual(expected["structural_hash"], structural_hash(workflow))
                self.assertEqual(expected_code, normalizer_node(workflow)["parameters"]["jsCode"])
                self.assertTrue({
                    "resolve_project",
                    "stop_instance",
                    "force_fail_instance",
                    "list_alert_groups",
                    "batch_update_schedule_alerts",
                }.issubset(actions(expected_code)))

    def test_latest_router_audits_batch_alert_updates_as_risky(self):
        workflow = json.loads(
            (ROOT / "n8n/ds-scheduler-router.latest.json").read_text(encoding="utf-8")
        )
        audit_node = next(
            node for node in workflow["nodes"] if node["name"] == "构造审计写入SQL"
        )
        code = audit_node["parameters"]["jsCode"]
        risk_body = re.search(r"const riskActions = new Set\(\[(.*?)\]\);", code, re.S).group(1)
        self.assertIn("batch_update_schedule_alerts", risk_body)


if __name__ == "__main__":
    unittest.main()
