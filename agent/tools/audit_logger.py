#!/usr/bin/env python3
"""
TOF Project Assistant - Audit Logger

Append-only JSONL audit log untuk mencatat semua event agent.
Setiap event dicatat dengan timestamp, actor, event type, dan metadata.

Usage:
    from audit_logger import AuditLogger
    logger = AuditLogger(state_dir="../../../state")
    logger.log(
        project_id="PRJ-001",
        event_type="task_received",
        actor="orchestrator",
        description="User submitted project brief",
        metadata={"brief_length": 500}
    )
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


class AuditLogger:
    def __init__(self, state_dir):
        self.audit_dir = Path(state_dir) / "audit-log"
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def log(self, project_id, event_type, actor, description, metadata=None, action_id=None, risk_level=None):
        timestamp = datetime.now(timezone.utc).isoformat()
        event_id = str(uuid.uuid4())
        
        event = {
            "id": event_id,
            "timestamp": timestamp,
            "projectId": project_id,
            "eventType": event_type,
            "actor": actor,
            "description": description,
            "metadata": metadata or {},
        }
        
        if action_id:
            event["actionId"] = action_id
        if risk_level:
            event["riskLevel"] = risk_level
        
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = self.audit_dir / f"{date_str}.jsonl"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        return event_id

    def read_today(self):
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.read_date(date_str)

    def read_date(self, date_str):
        log_file = self.audit_dir / f"{date_str}.jsonl"
        if not log_file.exists():
            return []
        
        events = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def read_project_events(self, project_id):
        all_events = []
        for log_file in sorted(self.audit_dir.glob("*.jsonl")):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        event = json.loads(line)
                        if event.get("projectId") == project_id:
                            all_events.append(event)
        return all_events

    def get_event_types(self):
        return [
            "task_received",
            "clarification_requested",
            "clarification_received",
            "plan_created",
            "plan_modified",
            "validation_started",
            "validation_completed",
            "risk_assessed",
            "approval_requested",
            "approval_granted",
            "approval_rejected",
            "execution_started",
            "execution_completed",
            "execution_failed",
            "tracker_sync_started",
            "tracker_sync_completed",
            "tracker_sync_failed",
            "conflict_detected",
            "closure_draft_created",
            "quotation_generated",
            "quotation_reviewed",
            "quotation_approved",
            "quotation_rejected",
            "quotation_email_prepared",
            "quotation_sent",
            "ui_spec_generated",
            "ui_screen_inventory_requested",
            "ui_screen_inventory_approved",
            "ui_screen_inventory_rejected",
            "ui_design_rendered",
            "ui_design_written",
            "ui_design_exported",
            "error",
        ]


if __name__ == "__main__":
    logger = AuditLogger("../../state")
    
    test_event_id = logger.log(
        project_id="PRJ-TEST",
        event_type="task_received",
        actor="orchestrator",
        description="Audit logger self-test: event logged successfully",
        metadata={"test": True}
    )
    
    print(f"Logged event: {test_event_id}")
    print(f"Today's events: {len(logger.read_today())}")
