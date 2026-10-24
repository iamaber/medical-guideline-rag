"""Knowledge-graph interaction tests."""

from src.services.medical_knowledge_graph import MedicalKnowledgeGraph


def test_known_interaction_is_reported_regardless_of_order():
    graph = MedicalKnowledgeGraph()
    forward = graph.analyze_drug_interactions(["aspirin", "warfarin"])
    reverse = graph.analyze_drug_interactions(["warfarin", "aspirin"])

    assert len(forward) == len(reverse) == 1
    assert forward[0]["severity"] == "major"
    assert forward[0]["description"]
    assert forward[0]["mechanism"]
    assert forward[0]["category"]


def test_unknown_pair_returns_no_interactions():
    graph = MedicalKnowledgeGraph()
    assert graph.analyze_drug_interactions(["aspirin", "paracetamol"]) == []


def test_single_medication_has_no_pairs():
    graph = MedicalKnowledgeGraph()
    assert graph.analyze_drug_interactions(["aspirin"]) == []
