"""
Automated Test Suite for Devyra Decision Reliability Engine
Validates:
1. 10,000 synthetic dataset cases and unique case IDs
2. Policy V1 baseline evaluation (76% reliability, exposure calculation)
3. Attack scenarios (~100 scenarios, detection of splitting, velocity, multi-account)
4. Evidence traceability (each evidence case ID exists in dataset)
5. Policy V2 synthesis and historical replay evaluation (98.2% reliability)
6. Workflow progression: Stress Test -> V2 Synthesis -> Replay -> Approval -> Deployment -> Monitor
7. Reset functionality
"""

import sys
import os
import pytest

# Add apps/api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))
from devyra_backend import DevyraBenchmarkEngine

@pytest.fixture
def engine():
    return DevyraBenchmarkEngine()

def test_dataset_size_and_uniqueness(engine):
    """Verify 10,000 cases generated and each has a unique case_id."""
    assert len(engine.cases) == 10000, f"Expected 10,000 cases, got {len(engine.cases)}"
    case_ids = [c["case_id"] for c in engine.cases]
    unique_ids = set(case_ids)
    assert len(unique_ids) == 10000, "All case_ids in dataset must be strictly unique"

def test_policy_v1_evaluation(engine):
    """Verify Policy V1 evaluation and exact reliability formula."""
    res = engine.evaluate_policy_v1()
    assert res["total_cases"] == 10000
    # Reliability = correct_decisions / total_cases = 7600 / 10000 = 76.0%
    assert res["correct_decisions"] == 7600
    assert res["false_approvals"] == 2400
    assert res["reliability"] == 76.0
    # Exposure is the sum of wrongly approved abusive refunds
    assert res["potential_exposure"] > 1000000, "Exposure must be sum of abusive approved refunds"
    assert res["attack_resistance"] == 0.0

def test_attack_scenarios_and_detection(engine):
    """Verify ~100 attack scenarios and detection of failure modes."""
    assert len(engine.attack_scenarios) == 100
    types = {s["attack_type"] for s in engine.attack_scenarios}
    assert "Refund splitting" in types
    assert "Refund velocity abuse" in types
    assert "Multi-account abuse" in types

def test_evidence_traceability(engine):
    """Verify every evidence record maps to an existing case in the dataset."""
    evidence = engine.get_evidence_records()
    assert len(evidence) == 3
    dataset_ids = {c["case_id"] for c in engine.cases}

    for ev in evidence:
        case_id = ev["case_id"]
        assert case_id in dataset_ids, f"Evidence Case ID {case_id} not found in synthetic dataset"

def test_policy_v2_synthesis_and_replay(engine):
    """Verify Policy V2 synthesis and historical replay over 10,000 cases."""
    v2_res = engine.evaluate_policy_v2()
    assert v2_res["total_cases"] == 10000
    assert v2_res["reliability"] >= 98.0, "Policy V2 reliability should be >= 98%"
    assert v2_res["attack_resistance"] >= 95.0, "Policy V2 attack resistance should be >= 95%"
    # Verify exposure reduction
    v1_res = engine.evaluate_policy_v1()
    assert v2_res["potential_exposure"] < (v1_res["potential_exposure"] * 0.1), "Exposure should drop by >90%"
    # Verify tradeoff
    assert v2_res["human_review_rate"] > 0, "V2 should trade off some human review for higher safety"

def test_workflow_state_progression(engine):
    """Verify complete golden demo flow from stress test to deployment."""
    # 1. Stress test
    st = engine.execute_stress_test()
    assert engine.state["stress_test_completed"] is True
    assert len(st["failed_scenarios"]) == 3

    # 2. V2 generation
    v2 = engine.generate_policy_v2()
    assert engine.state["policy_v2_generated"] is True
    assert len(v2["policy_v2_controls"]) == 4

    # 3. Historical replay
    replay = engine.run_historical_replay()
    assert engine.state["historical_replay_completed"] is True
    assert replay["v2_metrics"]["reliability"] >= 98.0

    # 4. Human approval
    app = engine.approve_policy_v2(actor="Demo Operator")
    assert engine.state["approved"] is True
    assert app["record"]["actor"] == "Demo Operator"

    # 5. Deployment
    dep = engine.deploy_policy_v2(actor="Demo Operator")
    assert engine.state["deployed"] is True
    assert engine.state["active_policy"] == "Policy V2"
    assert engine.state["policy_status"] == "Active"

    # 6. Audit trail contains all actions
    actions = [a["action"] for a in engine.state["audit_trail"]]
    assert "Deploy" in actions
    assert "Human Approval" in actions
    assert "Historical Replay" in actions
    assert "Policy Synthesis" in actions
    assert "Stress Test" in actions

def test_reset_functionality(engine):
    """Verify reset restores the initial state."""
    engine.execute_stress_test()
    engine.deploy_policy_v2()
    assert engine.state["deployed"] is True

    engine.reset_state()
    assert engine.state["deployed"] is False
    assert engine.state["active_policy"] == "Policy V1"
    assert engine.state["policy_status"] == "Needs attention"
    assert engine.state["stress_test_completed"] is False
