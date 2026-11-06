#!/usr/bin/env python3
"""
TOF Project Assistant - State Manager

Mengelola local JSON state untuk projects, approvals, dan execution history.
Read, create, update operasi untuk semua state files.

Usage:
    from state_manager import StateManager
    sm = StateManager("../../../state")
    
    project = sm.create_project("PRJ-001", "SG Garage WMS", brief_text="...")
    plan = sm.save_plan("PRJ-001", plan_dict)
    loaded = sm.load_project("PRJ-001")
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


class StateManager:
    def __init__(self, state_dir):
        self.state_dir = Path(state_dir)
        self.projects_dir = self.state_dir / "projects"
        self.pending_approvals_dir = self.state_dir / "pending-approvals"
        self.approval_history_dir = self.state_dir / "approval-history"
        self.execution_history_dir = self.state_dir / "execution-history"
        
        for d in [self.projects_dir, self.pending_approvals_dir, 
                   self.approval_history_dir, self.execution_history_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _project_path(self, project_id):
        return self.projects_dir / project_id

    def _ensure_project_dir(self, project_id):
        pdir = self._project_path(project_id)
        pdir.mkdir(parents=True, exist_ok=True)
        return pdir

    def create_project(self, project_id, project_name, brief_text=None, brief_file=None):
        pdir = self._ensure_project_dir(project_id)
        
        meta = {
            "projectId": project_id,
            "projectName": project_name,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "status": "brief_received",
            "currentStep": "receive_brief"
        }
        
        meta_path = pdir / "meta.json"
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        
        if brief_text:
            brief = {
                "projectId": project_id,
                "receivedAt": datetime.now(timezone.utc).isoformat(),
                "briefText": brief_text,
                "source": "user_input"
            }
            (pdir / "brief.json").write_text(
                json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        
        if brief_file and Path(brief_file).exists():
            brief_text = Path(brief_file).read_text(encoding="utf-8")
            brief = {
                "projectId": project_id,
                "receivedAt": datetime.now(timezone.utc).isoformat(),
                "briefText": brief_text,
                "source": "file:" + brief_file
            }
            (pdir / "brief.json").write_text(
                json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        
        return meta

    def load_project(self, project_id):
        pdir = self._project_path(project_id)
        if not pdir.exists():
            return None
        
        result = {}
        for f in pdir.glob("*.json"):
            result[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        return result

    def update_meta(self, project_id, updates):
        pdir = self._project_path(project_id)
        meta_path = pdir / "meta.json"
        
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            meta = {"projectId": project_id}
        
        meta.update(updates)
        meta["updatedAt"] = datetime.now(timezone.utc).isoformat()
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        return meta

    def save_clarifications(self, project_id, questions, answers):
        pdir = self._ensure_project_dir(project_id)
        
        clarifications = {
            "projectId": project_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "qa": [
                {"question": q, "answer": a} for q, a in zip(questions, answers)
            ]
        }
        
        path = pdir / "clarifications.json"
        path.write_text(json.dumps(clarifications, indent=2, ensure_ascii=False), encoding="utf-8")
        return clarifications

    def save_plan(self, project_id, plan):
        pdir = self._ensure_project_dir(project_id)
        path = pdir / "plan.json"
        path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
        
        self.update_meta(project_id, {
            "status": "plan_generated",
            "currentStep": "validation"
        })
        return plan

    def save_validation(self, project_id, validation_report):
        pdir = self._ensure_project_dir(project_id)
        path = pdir / "validation.json"
        path.write_text(json.dumps(validation_report, indent=2, ensure_ascii=False), encoding="utf-8")
        
        self.update_meta(project_id, {
            "status": "validated",
            "currentStep": "approval"
        })
        return validation_report

    def create_approval(self, project_id, action_type, target, detail_changes, 
                         sources=None, assumptions=None, expected_impact=None):
        timestamp = datetime.now(timezone.utc)
        action_id = f"ACT-{timestamp.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        approval = {
            "actionId": action_id,
            "projectId": project_id,
            "actionType": action_type,
            "target": target,
            "detailChanges": detail_changes,
            "sources": sources or [],
            "assumptions": assumptions or [],
            "expectedImpact": expected_impact or "",
            "approvalStatus": "PENDING_APPROVAL",
            "createdAt": timestamp.isoformat(),
            "approvedBy": None,
            "approvedAt": None,
            "executedAt": None,
            "verificationResult": None
        }
        
        path = self.pending_approvals_dir / f"{action_id}.json"
        path.write_text(json.dumps(approval, indent=2, ensure_ascii=False), encoding="utf-8")
        return approval

    def get_pending_approvals(self, project_id=None):
        approvals = []
        for f in self.pending_approvals_dir.glob("*.json"):
            approval = json.loads(f.read_text(encoding="utf-8"))
            if project_id is None or approval.get("projectId") == project_id:
                approvals.append(approval)
        return approvals

    def resolve_approval(self, action_id, decision, approved_by="user"):
        path = self.pending_approvals_dir / f"{action_id}.json"
        if not path.exists():
            return None
        
        approval = json.loads(path.read_text(encoding="utf-8"))
        
        if decision == "approved":
            approval["approvalStatus"] = "APPROVED"
            approval["approvedBy"] = approved_by
            approval["approvedAt"] = datetime.now(timezone.utc).isoformat()
        elif decision == "rejected":
            approval["approvalStatus"] = "REJECTED"
            approval["approvedBy"] = approved_by
            approval["approvedAt"] = datetime.now(timezone.utc).isoformat()
        else:
            return None
        
        project_id = approval.get("projectId", "unknown")
        history_dir = self.approval_history_dir / project_id
        history_dir.mkdir(parents=True, exist_ok=True)
        
        history_path = history_dir / f"{action_id}.json"
        history_path.write_text(json.dumps(approval, indent=2, ensure_ascii=False), encoding="utf-8")
        
        path.unlink()
        
        return approval

    def mark_executed(self, action_id, success=True, verification_result=None):
        project_id = "unknown"
        for pdir in self.approval_history_dir.iterdir():
            if not pdir.is_dir():
                continue
            path = pdir / f"{action_id}.json"
            if path.exists():
                approval = json.loads(path.read_text(encoding="utf-8"))
                approval["approvalStatus"] = "EXECUTED" if success else "FAILED"
                approval["executedAt"] = datetime.now(timezone.utc).isoformat()
                approval["verificationResult"] = verification_result or ("verified" if success else "failed")
                project_id = approval.get("projectId", "unknown")
                path.write_text(json.dumps(approval, indent=2, ensure_ascii=False), encoding="utf-8")
                return approval
        return None

    def save_rejection_feedback(self, project_id, action_id, reason, feedback_text):
        """
        Save rejection feedback for remediation loop.

        When an approval is REJECTED, the user's feedback is stored
        so the agent can revise and resubmit.
        """
        pdir = self._ensure_project_dir(project_id)

        feedback = {
            "projectId": project_id,
            "actionId": action_id,
            "reason": reason,
            "feedbackText": feedback_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Append to rejection feedback file (can have multiple rejections)
        feedback_path = pdir / "rejection-feedback.json"
        existing = []
        if feedback_path.exists():
            existing = json.loads(feedback_path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = [existing]

        existing.append(feedback)
        feedback_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        return feedback

    def get_rejection_feedback(self, project_id):
        """Get all rejection feedback for a project."""
        pdir = self._project_path(project_id)
        feedback_path = pdir / "rejection-feedback.json"
        if not feedback_path.exists():
            return []
        return json.loads(feedback_path.read_text(encoding="utf-8"))

    def list_projects(self):
        projects = []
        for pdir in self.projects_dir.iterdir():
            if pdir.is_dir():
                meta_path = pdir / "meta.json"
                if meta_path.exists():
                    projects.append(json.loads(meta_path.read_text(encoding="utf-8")))
        return projects


if __name__ == "__main__":
    sm = StateManager("../../state")
    
    project = sm.create_project("PRJ-TEST", "Test Project", brief_text="This is a test brief.")
    print(f"Created: {project['projectId']} - {project['projectName']}")
    
    loaded = sm.load_project("PRJ-TEST")
    print(f"Loaded keys: {list(loaded.keys())}")
    
    approval = sm.create_approval(
        "PRJ-TEST", "create_plan", "state/projects/PRJ-TEST/plan.json",
        ["Create project plan with 5 phases"],
        sources=["brief", "clarification"],
        expected_impact="Plan will guide development"
    )
    print(f"Approval: {approval['actionId']} - {approval['approvalStatus']}")
    
    resolved = sm.resolve_approval(approval["actionId"], "approved")
    print(f"Resolved: {resolved['approvalStatus']}")
    
    pending = sm.get_pending_approvals()
    print(f"Pending approvals: {len(pending)}")
