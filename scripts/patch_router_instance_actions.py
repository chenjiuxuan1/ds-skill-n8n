#!/usr/bin/env python3
"""Patch the approved n8n Router baseline without rebuilding its graph."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


BASELINE_SHA256 = "16009d22a58df418684adfec09338ee804c6216c641e11cc1373ceb3baac4361"


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"expected exactly one Router source fragment: {old!r}")
    return source.replace(old, new, 1)


def patch_router(source_path: Path, output_path: Path) -> None:
    raw = source_path.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != BASELINE_SHA256:
        raise ValueError(
            f"unexpected Router baseline SHA-256: {actual_sha}; expected {BASELINE_SHA256}"
        )
    workflow = json.loads(raw)
    normalizers = [
        node for node in workflow.get("nodes", [])
        if node.get("name") == "解析并标准化请求"
    ]
    if len(normalizers) != 1:
        raise ValueError("expected exactly one 解析并标准化请求 node")
    code = normalizers[0]["parameters"]["jsCode"]
    code = replace_once(
        code,
        "  'retry_instance',\n",
        "  'retry_instance',\n  'stop_instance',\n  'force_fail_instance',\n",
    )
    code = replace_once(
        code,
        "  project_code: inputPayload.project_code || '',\n",
        (
            "  project_code: inputPayload.project_code || '',\n"
            "  project_name: inputPayload.project_name || '',\n"
        ),
    )
    code = replace_once(
        code,
        (
            "if (action === 'retry_instance') {\n"
            "  if (!payload.project_code) errors.push('retry_instance requires project_code');\n"
            "  if (!payload.instance_id) errors.push('retry_instance requires instance_id');\n"
            "}\n"
        ),
        (
            "if (['retry_instance', 'stop_instance', 'force_fail_instance'].includes(action)) {\n"
            "  if (!payload.project_code) errors.push(`${action} requires project_code`);\n"
            "  if (!payload.instance_id) errors.push(`${action} requires instance_id`);\n"
            "}\n"
            "if (action === 'resolve_project' && !payload.project_code && !payload.project_name) {\n"
            "  errors.push('resolve_project requires project_code or project_name');\n"
            "}\n"
        ),
    )
    normalizers[0]["parameters"]["jsCode"] = code
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(workflow, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    patch_router(args.source, args.output)


if __name__ == "__main__":
    main()
