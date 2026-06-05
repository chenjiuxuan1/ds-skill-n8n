#!/usr/bin/env python3
"""Build standardized DS scheduler webhook payloads and curl commands."""

from __future__ import annotations

import argparse
import json
import shlex
from datetime import datetime
from typing import Any, Dict


COUNTRIES = {"cn", "ine", "mx", "ph", "pk", "th"}
ACTIONS = {
    "list_workflows",
    "get_workflow",
    "online_workflow",
    "offline_workflow",
    "trigger_workflow",
    "list_instances",
    "get_instance",
}


def _load_json(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    return json.loads(raw)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    _require(args.country in COUNTRIES, f"Unsupported country: {args.country}")
    _require(args.action in ACTIONS, f"Unsupported action: {args.action}")
    _require(bool(args.ds_token), "ds_token is required")

    if args.action in {"online_workflow", "offline_workflow", "trigger_workflow"}:
        _require(bool(args.workflow_code), f"{args.action} requires --workflow-code")
    if args.action == "get_instance":
        _require(bool(args.instance_id), "get_instance requires --instance-id")
    if args.action == "get_workflow":
        _require(bool(args.workflow_code or args.workflow_name), "get_workflow requires --workflow-code or --workflow-name")

    payload = {
        "source": "codex-skill",
        "country": args.country,
        "action": args.action,
        "ds_token": args.ds_token,
        "request_id": args.request_id or datetime.now().strftime("%Y%m%d-%H%M%S"),
        "payload": {
            "project_code": args.project_code or "",
            "workflow_code": args.workflow_code or "",
            "workflow_name": args.workflow_name or "",
            "instance_id": args.instance_id or "",
            "start_node_list": args.start_node_list or "",
            "schedule_time": args.schedule_time or "",
            "state_type": args.state_type or "",
            "search_val": args.search_val or "",
            "page_no": args.page_no,
            "page_size": args.page_size,
            "custom_params": _load_json(args.custom_params_json, {}),
        },
    }
    return payload


def build_curl(webhook_url: str, payload: Dict[str, Any]) -> str:
    body = json.dumps(payload, ensure_ascii=False)
    return (
        f"curl -X POST {shlex.quote(webhook_url)} "
        f"-H 'Content-Type: application/json' "
        f"-d {shlex.quote(body)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build DS scheduler webhook payload")
    parser.add_argument("--webhook-url", required=True)
    parser.add_argument("--country", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--ds-token", required=True)
    parser.add_argument("--request-id")
    parser.add_argument("--project-code")
    parser.add_argument("--workflow-code")
    parser.add_argument("--workflow-name")
    parser.add_argument("--instance-id")
    parser.add_argument("--start-node-list")
    parser.add_argument("--schedule-time")
    parser.add_argument("--state-type")
    parser.add_argument("--search-val")
    parser.add_argument("--page-no", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--custom-params-json")
    args = parser.parse_args()

    payload = build_payload(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print()
    print("# curl")
    print(build_curl(args.webhook_url, payload))


if __name__ == "__main__":
    main()
