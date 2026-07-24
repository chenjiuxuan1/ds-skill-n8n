import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path("/Users/jiangchuanchen/Downloads/ds-scheduler-router (2).json")
ARTIFACT = ROOT / "n8n/ds-scheduler-router.latest.json"


def actions(workflow):
    node = next(node for node in workflow["nodes"] if node["name"] == "解析并标准化请求")
    code = node["parameters"]["jsCode"]
    body = re.search(r"const ACTIONS = new Set\(\[(.*?)\]\);", code, re.S).group(1)
    return set(re.findall(r"'([^']+)'", body))


class RouterArtifactTests(unittest.TestCase):
    def test_artifact_is_incremental_patch_of_approved_baseline(self):
        self.assertEqual(
            "16009d22a58df418684adfec09338ee804c6216c641e11cc1373ceb3baac4361",
            hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
        )
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(24, len(artifact["nodes"]))
        self.assertEqual(19, len(artifact["connections"]))
        self.assertEqual(
            actions(baseline) | {"stop_instance", "force_fail_instance"},
            actions(artifact),
        )
        self.assertEqual(baseline["connections"], artifact["connections"])
        before = {node["name"]: node for node in baseline["nodes"]}
        after = {node["name"]: node for node in artifact["nodes"]}
        for name in before:
            if name == "解析并标准化请求":
                continue
            self.assertEqual(before[name], after[name], name)
        self.assertEqual(
            before["解析并标准化请求"]["id"],
            after["解析并标准化请求"]["id"],
        )
        self.assertIn("resolve_project", actions(artifact))


if __name__ == "__main__":
    unittest.main()
