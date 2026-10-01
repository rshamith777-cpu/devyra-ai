"""
Devyra — FastAPI Application
Endpoints for AI Decision Reliability Platform (ApexCloud · Customer Refund Approval)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import sys

# Add parent directory to path to enable direct execution
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from devyra_backend import devyra_engine

app = FastAPI(
    title="Devyra API",
    description="AI Decision Reliability Platform API for GIBC V2",
    version="1.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ApprovalRequest(BaseModel):
    actor: str = "Demo Operator"

@app.get("/api/devyra/overview")
def get_overview():
    v1 = devyra_engine.state["v1_metrics"]
    v2 = devyra_engine.state["v2_metrics"]
    is_deployed = devyra_engine.state["deployed"]

    active_metrics = v2 if is_deployed else v1
    vulns = 0 if is_deployed else 3
    status = "Active" if is_deployed else "Needs attention"

    return {
        "company": devyra_engine.company,
        "decision": devyra_engine.decision,
        "environment": devyra_engine.environment,
        "status": status,
        "primary_reliability": active_metrics["reliability"],
        "active_vulnerabilities": vulns,
        "historical_cases": active_metrics["total_cases"],
        "potential_exposure": active_metrics["potential_exposure"],
        "question": "What should I worry about today?",
        "deployed": is_deployed,
        "active_policy": devyra_engine.state["active_policy"]
    }

@app.get("/api/devyra/decision/refund")
def get_decision():
    v1 = devyra_engine.state["v1_metrics"]
    return {
        "title": "Customer Refund Approval",
        "subtitle": "ApexCloud · Automated business decision",
        "current_policy": "Policy V1",
        "policy_rule": "Approve when: refund_amount <= 500 AND customer_account_age_days >= 30 AND refund_count_30d < 3",
        "metrics": v1,
        "status": devyra_engine.state["policy_status"]
    }

@app.post("/api/devyra/stress-test")
def run_stress_test():
    result = devyra_engine.execute_stress_test()
    return result

@app.get("/api/devyra/evidence/{case_id}")
def get_evidence(case_id: str):
    for ev in devyra_engine.state["evidence"]:
        if ev["case_id"] == case_id:
            return ev
    raise HTTPException(status_code=404, detail=f"Case ID {case_id} not found")

@app.post("/api/devyra/generate-policy")
def generate_policy():
    result = devyra_engine.generate_policy_v2()
    return result

@app.post("/api/devyra/historical-replay")
def run_historical_replay():
    result = devyra_engine.run_historical_replay()
    return result

@app.get("/api/devyra/policies/compare")
def compare_policies():
    v1 = devyra_engine.state["v1_metrics"]
    v2 = devyra_engine.state["v2_metrics"] or devyra_engine.evaluate_policy_v2()
    return {
        "v1": v1,
        "v2": v2,
        "tradeoff_analysis": "Policy V2 reduces abusive approvals by 96.7% (saving ₹11,24,200) with an operational tradeoff of increasing human review by 8.2%."
    }

@app.post("/api/devyra/approve")
def approve_policy(req: ApprovalRequest):
    result = devyra_engine.approve_policy_v2(actor=req.actor)
    return result

@app.post("/api/devyra/deploy")
def deploy_policy(req: ApprovalRequest):
    result = devyra_engine.deploy_policy_v2(actor=req.actor)
    return result

@app.get("/api/devyra/monitor")
def get_monitor():
    v1 = devyra_engine.state["v1_metrics"]
    v2 = devyra_engine.state["v2_metrics"] or devyra_engine.evaluate_policy_v2()
    current = v2 if devyra_engine.state["deployed"] else v1

    return {
        "active_policy": devyra_engine.state["active_policy"],
        "metrics": current,
        "active_alerts": 0,
        "activity_feed": devyra_engine.state["activity_feed"]
    }

@app.get("/api/devyra/audit")
def get_audit():
    return {
        "audit_trail": devyra_engine.state["audit_trail"]
    }

@app.post("/api/devyra/reset")
def reset_state():
    devyra_engine.reset_state()
    return {"status": "reset", "message": "Demo state restored to initial baseline."}

# Mount static files and index.html if running from workspace root
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
assets_dir = os.path.join(root_dir, "assets")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
def serve_root():
    index_path = os.path.join(root_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Devyra API running. index.html not found at root."}
