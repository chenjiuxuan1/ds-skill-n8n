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
        "structural_hash": "ca5755fd4ba58b1f1e17c32509f224fba24abda0fb63e1be3f7392879b1d94de",
    },
    ROOT / "n8n/ds-scheduler-router.latest.json": {
        "nodes": 24,
        "connections": 19,
        "structural_hash": "55b639ca15ced964b5bfe3c37ae9a29cfaf2409d34ef9fa8a61d6f21e5f82cd6",
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
                    "update_workflow_environment",
                    "batch_update_workflow_environment",
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
        self.assertIn("update_workflow_environment", risk_body)
        self.assertIn("batch_update_workflow_environment", risk_body)
        # Environment switching is a definition rewrite, not a destructive op.
        high_risk_body = re.search(
            r"const highRiskActions = new Set\(\[(.*?)\]\);", code, re.S
        ).group(1)
        self.assertNotIn("update_workflow_environment", high_risk_body)
        self.assertNotIn("batch_update_workflow_environment", high_risk_body)


class CodePullCommandTests(unittest.TestCase):
    """The code-pull nodes are how a host receives every other fix.

    They used to run ``git remote remove`` before ``git remote add``, which
    threw away a working remote (and any credential configured on it) every
    time, and one node pointed at an internal SSH URL that needs a deploy key
    the host may not have. Both made the pull fail exactly when it was needed.
    """

    def _commands(self):
        for path in ARTIFACTS:
            workflow = json.loads(path.read_text(encoding="utf-8"))
            for node in workflow["nodes"]:
                command = (node.get("parameters") or {}).get("command")
                if command and "git remote" in command:
                    yield path.name, node["name"], command

    def test_no_node_deletes_a_remote_before_adding_it(self):
        for artifact, name, command in self._commands():
            with self.subTest(artifact=artifact, node=name):
                self.assertNotIn("git remote remove", command)

    def test_no_node_depends_on_the_internal_ssh_remote(self):
        for artifact, name, command in self._commands():
            with self.subTest(artifact=artifact, node=name):
                self.assertNotIn("git@git.kuainiujinke.com", command)

    def test_every_pull_node_is_idempotent(self):
        # "get-url ... || add" keeps an existing remote (and its credentials).
        for artifact, name, command in self._commands():
            with self.subTest(artifact=artifact, node=name):
                self.assertIn("git remote get-url", command)

    def test_every_pull_node_reports_the_resulting_commit(self):
        for artifact, name, command in self._commands():
            with self.subTest(artifact=artifact, node=name):
                self.assertIn("git rev-parse --short HEAD", command)

    def test_every_pull_node_covers_all_six_countries(self):
        for path in ARTIFACTS:
            workflow = json.loads(path.read_text(encoding="utf-8"))
            pulls = [
                node["name"] for node in workflow["nodes"]
                if "拉取代码" in node["name"] or "代码拉取" in node["name"]
            ]
            with self.subTest(artifact=path.name):
                self.assertEqual(6, len(pulls), pulls)

    def test_dead_legacy_router_is_gone(self):
        # It hardcoded personal absolute paths and the pre-PK DS API, and
        # nothing referenced it.
        self.assertFalse((ROOT / "n8n/ds_scheduler_router.py").exists())

    def test_no_tracked_file_leaks_a_personal_home_path(self):
        # Built at runtime so this test file does not itself contain the needle.
        needle = "/Users/" + "jiangchuanchen"
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git/" in str(path):
                continue
            if path.suffix in {".pyc", ".zip"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if needle in text:
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
