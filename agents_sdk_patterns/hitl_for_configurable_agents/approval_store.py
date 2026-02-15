"""
approval_store.py - Persistence for approval requests and decisions.

Two implementations:
  1) InMemoryApprovalStore  -> for tests + sync CLI examples
  2) FileApprovalStore      -> for async queue example (JSON file)

Both implement the same interface:
  - save_request(request)
  - get_request(request_id) -> request
  - save_decision(decision)
  - get_decision(request_id) -> decision or None
  - wait_for_decision(request_id, timeout) -> decision or timeout
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Optional

from schemas import ApprovalDecision, ApprovalRequest


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# In-Memory Store (tests + sync examples)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class InMemoryApprovalStore:
    """
    Stores requests and decisions in dictionaries.
    Fast, ephemeral, perfect for single-process examples.
    """

    def __init__(self):
        self._requests: Dict[str, ApprovalRequest] = {}
        self._decisions: Dict[str, ApprovalDecision] = {}

    def save_request(self, request: ApprovalRequest) -> None:
        self._requests[request.request_id] = request

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        return self._requests.get(request_id)

    def save_decision(self, decision: ApprovalDecision) -> None:
        self._decisions[decision.request_id] = decision

    def get_decision(self, request_id: str) -> Optional[ApprovalDecision]:
        return self._decisions.get(request_id)

    def wait_for_decision(
        self, request_id: str, timeout_seconds: int = 60
    ) -> Optional[ApprovalDecision]:
        """
        Poll for a decision until it appears or timeout.
        Used by the async queue mode.
        """
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            decision = self.get_decision(request_id)
            if decision is not None:
                return decision
            time.sleep(0.5)  # poll interval
        return None

    def list_pending(self) -> list[ApprovalRequest]:
        """Return requests that don't have a decision yet."""
        return [
            req for rid, req in self._requests.items()
            if rid not in self._decisions
        ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# File-Based Store (async queue example)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class FileApprovalStore:
    """
    Stores requests/decisions as JSON files in a directory.
    Enables cross-process async: agent writes request, approver reads + decides.

    File layout:
      {base_dir}/requests/{request_id}.json
      {base_dir}/decisions/{request_id}.json
    """

    def __init__(self, base_dir: str = "/tmp/hitl_store"):
        self.base_dir = Path(base_dir)
        self._req_dir = self.base_dir / "requests"
        self._dec_dir = self.base_dir / "decisions"
        self._req_dir.mkdir(parents=True, exist_ok=True)
        self._dec_dir.mkdir(parents=True, exist_ok=True)

    def save_request(self, request: ApprovalRequest) -> None:
        path = self._req_dir / f"{request.request_id}.json"
        path.write_text(request.model_dump_json(indent=2))

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        path = self._req_dir / f"{request_id}.json"
        if not path.exists():
            return None
        return ApprovalRequest.model_validate_json(path.read_text())

    def save_decision(self, decision: ApprovalDecision) -> None:
        path = self._dec_dir / f"{decision.request_id}.json"
        path.write_text(decision.model_dump_json(indent=2))

    def get_decision(self, request_id: str) -> Optional[ApprovalDecision]:
        path = self._dec_dir / f"{request_id}.json"
        if not path.exists():
            return None
        return ApprovalDecision.model_validate_json(path.read_text())

    def wait_for_decision(
        self, request_id: str, timeout_seconds: int = 60
    ) -> Optional[ApprovalDecision]:
        """Poll the decisions directory until file appears or timeout."""
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            decision = self.get_decision(request_id)
            if decision is not None:
                return decision
            time.sleep(0.5)
        return None

    def list_pending(self) -> list[ApprovalRequest]:
        """Return requests without a matching decision file."""
        pending = []
        for req_file in self._req_dir.glob("*.json"):
            rid = req_file.stem
            dec_file = self._dec_dir / f"{rid}.json"
            if not dec_file.exists():
                pending.append(ApprovalRequest.model_validate_json(req_file.read_text()))
        return pending
