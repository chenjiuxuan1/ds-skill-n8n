#!/usr/bin/env python3
"""Synchronize request validation into checked-in n8n artifacts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NORMALIZER = ROOT / "n8n/request_normalizer.js"
ARTIFACTS = (
    ROOT / "n8n/workflow-template.json",
    ROOT / "n8n/ds-scheduler-router.latest.json",
)

# Write actions that the audit node must classify as "medium" risk. They are
# inserted after the ``update_schedule`` anchor so re-running this script stays
# idempotent.
AUDIT_ACTION_ANCHOR = "  'update_schedule',\n"
AUDIT_RISK_ACTIONS = (
    "batch_update_schedule_alerts",
    "update_workflow_environment",
    "batch_update_workflow_environment",
)


def node_named(workflow: dict, name: str) -> dict:
    matches = [node for node in workflow.get("nodes", []) if node.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one n8n node named {name!r}")
    return matches[0]


def sync_audit_risk_actions(code: str) -> str:
    # Insert in reverse so the final order matches AUDIT_RISK_ACTIONS.
    for action in reversed(AUDIT_RISK_ACTIONS):
        if f"'{action}'" in code:
            continue
        if code.count(AUDIT_ACTION_ANCHOR) != 1:
            raise ValueError("expected one update_schedule audit action anchor")
        code = code.replace(
            AUDIT_ACTION_ANCHOR,
            AUDIT_ACTION_ANCHOR + f"  '{action}',\n",
            1,
        )
    return code


def sync_artifact(path: Path, normalizer: str) -> None:
    workflow = json.loads(path.read_text(encoding="utf-8"))
    node_named(workflow, "解析并标准化请求")["parameters"]["jsCode"] = normalizer
    if path.name == "ds-scheduler-router.latest.json":
        audit_node = node_named(workflow, "构造审计写入SQL")
        audit_node["parameters"]["jsCode"] = sync_audit_risk_actions(
            audit_node["parameters"]["jsCode"]
        )
    path.write_text(
        json.dumps(workflow, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    normalizer = NORMALIZER.read_text(encoding="utf-8")
    for path in ARTIFACTS:
        sync_artifact(path, normalizer)


if __name__ == "__main__":
    main()
