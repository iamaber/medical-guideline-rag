"""Medical Knowledge Graph for understanding drug-disease-concept relationships."""

import logging
import networkx as nx
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MedicalKnowledgeGraph:
    """Medical knowledge graph for understanding drug-disease-concept relationships."""

    def __init__(self):
        self.graph = nx.Graph()
        self.drug_interactions = {}
        self.therapeutic_classes = {}
        self.indication_mappings = {}
        self._load_medical_ontology()

    def _load_medical_ontology(self):
        """Load medical ontology data into graph."""
        try:
            # Load basic drug classification data
            self._load_drug_classifications()

            # Load known drug interactions
            self._load_drug_interactions()

            # Load therapeutic indications
            self._load_therapeutic_indications()

            logger.info(
                f"Loaded medical knowledge graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges"
            )

        except Exception as e:
            logger.error(f"Error loading medical ontology: {e}")

    def _load_drug_classifications(self):
        """Load drug classification data."""
        # Basic drug classes - this would typically come from a medical database
        drug_classes = {
            "aspirin": ["antiplatelet", "analgesic", "anti-inflammatory"],
            "metformin": ["antidiabetic", "biguanide"],
            "lisinopril": ["ace_inhibitor", "antihypertensive"],
            "atorvastatin": ["statin", "lipid_lowering"],
            "levothyroxine": ["thyroid_hormone", "hormone_replacement"],
            "metoprolol": ["beta_blocker", "antihypertensive"],
            "amlodipine": ["calcium_channel_blocker", "antihypertensive"],
            "omeprazole": ["proton_pump_inhibitor", "acid_reducer"],
            "warfarin": ["anticoagulant", "blood_thinner"],
            "insulin": ["antidiabetic", "hormone"],
        }

        for drug, classes in drug_classes.items():
            # Add drug node
            self.graph.add_node(drug, type="drug")

            # Add class nodes and connections
            for drug_class in classes:
                self.graph.add_node(drug_class, type="drug_class")
                self.graph.add_edge(drug, drug_class, relationship="belongs_to_class")

            # Store for quick lookup
            self.therapeutic_classes[drug] = classes

    def _load_drug_interactions(self):
        """Load known drug interaction data."""
        # Basic interaction data - this would come from a medical database
        interactions = {
            ("warfarin", "aspirin"): {"severity": "major", "risk": "bleeding"},
            ("warfarin", "omeprazole"): {
                "severity": "moderate",
                "risk": "altered_anticoagulation",
            },
            ("metformin", "insulin"): {"severity": "minor", "risk": "hypoglycemia"},
            ("lisinopril", "metoprolol"): {"severity": "minor", "risk": "hypotension"},
            ("atorvastatin", "amlodipine"): {
                "severity": "moderate",
                "risk": "muscle_toxicity",
            },
        }

        for (drug1, drug2), interaction_data in interactions.items():
            # Add interaction edge
            if self.graph.has_node(drug1) and self.graph.has_node(drug2):
                self.graph.add_edge(
                    drug1,
                    drug2,
                    relationship="interacts_with",
                    severity=interaction_data["severity"],
                    risk=interaction_data["risk"],
                )

            # Store for quick lookup
            interaction_key = tuple(sorted([drug1, drug2]))
            self.drug_interactions[interaction_key] = interaction_data

    def _load_therapeutic_indications(self):
        """Load therapeutic indication mappings."""
        indications = {
            "aspirin": [
                "cardiovascular_disease",
                "pain",
                "inflammation",
                "stroke_prevention",
            ],
            "metformin": ["type2_diabetes", "prediabetes", "pcos"],
            "lisinopril": ["hypertension", "heart_failure", "diabetic_nephropathy"],
            "atorvastatin": [
                "hyperlipidemia",
                "cardiovascular_disease",
                "stroke_prevention",
            ],
            "levothyroxine": ["hypothyroidism", "thyroid_cancer"],
            "metoprolol": ["hypertension", "heart_failure", "angina", "arrhythmia"],
            "amlodipine": ["hypertension", "angina"],
            "omeprazole": ["gerd", "peptic_ulcer", "acid_reflux"],
            "warfarin": [
                "atrial_fibrillation",
                "deep_vein_thrombosis",
                "pulmonary_embolism",
            ],
            "insulin": ["type1_diabetes", "type2_diabetes"],
        }

        for drug, conditions in indications.items():
            # Add condition nodes and connections
            for condition in conditions:
                self.graph.add_node(condition, type="condition")
                if self.graph.has_node(drug):
                    self.graph.add_edge(drug, condition, relationship="treats")

            # Store for quick lookup
            self.indication_mappings[drug] = conditions

    def find_related_concepts(self, medication: str, depth: int = 2) -> List[str]:
        """Find related medical concepts for a medication."""
        medication = medication.lower()
        related_concepts = []

        if medication in self.graph:
            # Find concepts within specified depth
            try:
                neighbors = nx.single_source_shortest_path_length(
                    self.graph, medication, cutoff=depth
                )
                related_concepts = [
                    node for node in neighbors.keys() if node != medication
                ]
            except nx.NetworkXError:
                pass

        return related_concepts

    def get_pharmacological_class(self, medication: str) -> List[str]:
        """Get pharmacological class for a medication."""
        medication = medication.lower()
        return self.therapeutic_classes.get(medication, [])

    def get_therapeutic_indications(self, medication: str) -> List[str]:
        """Get therapeutic indications for a medication."""
        medication = medication.lower()
        return self.indication_mappings.get(medication, [])

    def get_therapeutic_pathways(self, medications: List[str]) -> Dict[str, List[str]]:
        """Get therapeutic pathways for medication combinations."""
        pathways = {}

        for med in medications:
            med = med.lower()
            if med in self.graph:
                # Find therapeutic targets and pathways
                pathways[med] = self._get_pathways_for_drug(med)

        return pathways

    def _get_pathways_for_drug(self, medication: str) -> List[str]:
        """Get therapeutic pathways for a specific drug."""
        pathways = []

        if medication in self.graph:
            # Get connected conditions and drug classes
            neighbors = list(self.graph.neighbors(medication))
            for neighbor in neighbors:
                edge_data = self.graph.get_edge_data(medication, neighbor)
                if edge_data and edge_data.get("relationship") in [
                    "treats",
                    "belongs_to_class",
                ]:
                    pathways.append(neighbor)

        return pathways

    def analyze_drug_interactions(self, medications: List[str]) -> List[Dict]:
        """Analyze potential drug-drug interactions."""
        interactions = []
        medications = [med.lower() for med in medications]

        for i, med1 in enumerate(medications):
            for med2 in medications[i + 1 :]:
                interaction = self.get_drug_interaction(med1, med2)
                if interaction:
                    interactions.append({"drug1": med1, "drug2": med2, **interaction})

        return interactions

    def get_drug_interaction(self, med1: str, med2: str) -> Optional[Dict]:
        """Get interaction information between two medications."""
        interaction_key = tuple(sorted([med1.lower(), med2.lower()]))
        return self.drug_interactions.get(interaction_key)

    def calculate_interaction_risk(self, med1: str, med2: str) -> float:
        """Calculate interaction risk between two medications."""
        med1, med2 = med1.lower(), med2.lower()

        if med1 in self.graph and med2 in self.graph:
            try:
                # Calculate shortest path as proxy for interaction risk
                path_length = nx.shortest_path_length(self.graph, med1, med2)
                # Inverse relationship: shorter path = higher risk
                return 1.0 / (path_length + 1)
            except nx.NetworkXNoPath:
                return 0.0
        return 0.0

    def get_contraindications(
        self, medication: str, patient_conditions: List[str] = None
    ) -> List[str]:
        """Get contraindications for a medication based on patient conditions."""
        contraindications = []
        medication = medication.lower()

        # Basic contraindications (would be loaded from medical database)
        basic_contraindications = {
            "warfarin": ["pregnancy", "active_bleeding", "severe_liver_disease"],
            "aspirin": ["active_bleeding", "severe_asthma", "children_under_16"],
            "metformin": ["severe_kidney_disease", "liver_disease", "heart_failure"],
            "lisinopril": [
                "pregnancy",
                "angioedema_history",
                "bilateral_renal_stenosis",
            ],
            "atorvastatin": ["active_liver_disease", "pregnancy", "breastfeeding"],
        }

        contraindications.extend(basic_contraindications.get(medication, []))

        # Check patient-specific contraindications
        if patient_conditions:
            patient_conditions = [condition.lower() for condition in patient_conditions]
            for contraindication in contraindications:
                if contraindication in patient_conditions:
                    contraindications.append(f"CONTRAINDICATED: {contraindication}")

        return contraindications

    def get_monitoring_parameters(self, medications: List[str]) -> Dict[str, List[str]]:
        """Get monitoring parameters for medications."""
        monitoring = {}

        monitoring_data = {
            "warfarin": ["INR", "bleeding_signs", "CBC"],
            "atorvastatin": ["liver_enzymes", "CK", "lipid_panel"],
            "metformin": ["kidney_function", "B12_levels", "blood_glucose"],
            "lisinopril": ["kidney_function", "potassium", "blood_pressure"],
            "levothyroxine": ["TSH", "T4", "heart_rate"],
        }

        for med in medications:
            med = med.lower()
            if med in monitoring_data:
                monitoring[med] = monitoring_data[med]

        return monitoring

    def get_stats(self) -> Dict:
        """Get knowledge graph statistics."""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "drug_nodes": len(
                [n for n, d in self.graph.nodes(data=True) if d.get("type") == "drug"]
            ),
            "condition_nodes": len(
                [
                    n
                    for n, d in self.graph.nodes(data=True)
                    if d.get("type") == "condition"
                ]
            ),
            "drug_class_nodes": len(
                [
                    n
                    for n, d in self.graph.nodes(data=True)
                    if d.get("type") == "drug_class"
                ]
            ),
            "known_interactions": len(self.drug_interactions),
            "therapeutic_mappings": len(self.indication_mappings),
        }
