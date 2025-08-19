import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from config.settings import (
    PROCESSED_DIR,
    EMBEDDING_MODEL,
    VECTOR_SEARCH_TOP_K,
    FAISS_INDEX_PATH,
    DOCUMENTS_METADATA_PATH,
)
from .medical_knowledge_graph import MedicalKnowledgeGraph

logger = logging.getLogger(__name__)


class VectorSearch:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or EMBEDDING_MODEL
        self.model = None
        self.index = None
        self.documents = []
        self.embeddings = None
        self.knowledge_graph = MedicalKnowledgeGraph()
        self._load_model()

    def _load_model(self):
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded sentence transformer model: {self.model_name}")
        except ImportError:
            logger.error("sentence-transformers not installed")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")

    def load_processed_data(self, data_dir: str = None) -> None:
        if not self.model:
            logger.error("Model not loaded. Cannot process documents.")
            return

        data_path = Path(data_dir) if data_dir else PROCESSED_DIR
        documents = []

        logger.info(f"Loading documents from: {data_path}")

        # Load all JSON files from processed directory
        json_files = list(data_path.glob("*.json"))
        if not json_files:
            logger.warning(f"No JSON files found in {data_path}")
            return

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Handle different data formats
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            doc = self._format_document(item, json_file.name)
                            if doc:
                                # Handle both single docs and lists of docs from hierarchical chunking
                                if isinstance(doc, list):
                                    documents.extend(doc)
                                else:
                                    documents.append(doc)
                elif isinstance(data, dict):
                    doc = self._format_document(data, json_file.name)
                    if doc:
                        # Handle both single docs and lists of docs from hierarchical chunking
                        if isinstance(doc, list):
                            documents.extend(doc)
                        else:
                            documents.append(doc)

            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        self.documents = documents
        logger.info(f"Loaded {len(documents)} documents")

        if documents:
            self._create_index()
        else:
            logger.warning("No documents loaded for indexing")

    def _format_document(self, item: Dict, source_file: str) -> Optional[Dict]:
        """Format document for indexing with medical section awareness."""
        # Handle PubMed articles format with enhanced section processing
        if "pmid" in item:
            sections = self._extract_medical_sections(item)

            formatted_docs = []
            for section_type, content in sections.items():
                if content:
                    doc = {
                        "id": f"{item['pmid']}_{section_type}",
                        "title": item.get("title", ""),
                        "content": content,
                        "source": item.get("source", source_file),
                        "source_type": "pubmed_article",
                        "section_type": section_type,
                        "section_priority": self._get_section_priority(section_type),
                        "mesh_terms": item.get("mesh_terms", []),
                        "publication_year": item.get("year", 0),
                        "abstract": item.get("abstract", ""),
                        "publication_date": item.get("publication_date", ""),
                    }
                    formatted_docs.append(doc)
            return formatted_docs if formatted_docs else None

        # Handle WHO guidelines format
        elif "id" in item and "body" in item:
            title = item.get("title", "")
            body = item.get("body", "")

            # For WHO guidelines, use title + body
            text_content = f"{title}. {body}" if title and body else (title or body)

            if not text_content:
                return None

            return {
                "id": str(item["id"]),
                "title": title,
                "content": text_content,
                "source": item.get("source", source_file),
                "source_type": "who_guideline",
                "section_type": "guideline",
                "section_priority": 4,
                "body": body,
                "keywords": item.get("keywords", []),
            }

        # Fallback for other formats
        else:
            content_fields = [
                "title",
                "abstract",
                "body",
                "content",
                "text",
                "description",
            ]
            text_content = ""

            for field in content_fields:
                if field in item and item[field]:
                    text_content = str(item[field])
                    break

            if not text_content:
                return None

            return {
                "id": str(item.get("id", item.get("pmid", item.get("guid", "")))),
                "title": str(item.get("title", "")),
                "content": text_content,
                "source": str(item.get("source", source_file)),
                "source_type": "processed_data",
                "section_type": "general",
                "section_priority": 2,
                "mesh_terms": item.get("mesh_terms", []),
                "keywords": item.get("keywords", []),
            }

    def _extract_medical_sections(self, item: Dict) -> Dict[str, str]:
        """Extract medical sections from document."""
        sections = {}

        title = item.get("title", "")
        abstract = item.get("abstract", "")

        # Identify section types based on content
        sections["title"] = title
        sections["abstract"] = abstract

        # Extract methodology, results, conclusions if available
        if abstract:
            abstract_lower = abstract.lower()
            if "methods" in abstract_lower or "methodology" in abstract_lower:
                sections["methodology"] = self._extract_section(abstract, "methods")
            if "results" in abstract_lower:
                sections["results"] = self._extract_section(abstract, "results")
            if "conclusion" in abstract_lower or "conclusions" in abstract_lower:
                sections["conclusions"] = self._extract_section(abstract, "conclusion")

        return sections

    def _extract_section(self, text: str, section_type: str) -> str:
        """Extract specific section from text."""
        text_lower = text.lower()
        section_keywords = {
            "methods": ["methods", "methodology", "design", "participants"],
            "results": ["results", "findings", "outcomes", "data"],
            "conclusion": ["conclusion", "conclusions", "summary", "implications"],
        }

        keywords = section_keywords.get(section_type, [])
        for keyword in keywords:
            if keyword in text_lower:
                # Simple extraction - in practice, this would be more sophisticated
                start_idx = text_lower.find(keyword)
                if start_idx != -1:
                    # Extract sentence containing the keyword and following sentences
                    sentences = text[start_idx:].split(".")
                    return (
                        ". ".join(sentences[:2]) + "."
                        if len(sentences) > 1
                        else sentences[0]
                    )

        return ""

    def _get_section_priority(self, section_type: str) -> int:
        """Assign priority scores to different medical sections."""
        priorities = {
            "conclusions": 5,
            "results": 4,
            "abstract": 3,
            "methodology": 2,
            "title": 1,
            "guideline": 4,
            "general": 2,
        }
        return priorities.get(section_type, 1)

    def _create_index(self) -> None:
        """Create FAISS index from documents."""
        try:
            import faiss
        except ImportError:
            logger.error("FAISS not installed. Install with: pip install faiss-cpu")
            return

        logger.info("Creating vector embeddings...")

        # Combine title and content for embedding with better text preparation
        texts = []
        for doc in self.documents:
            text_parts = []

            # Always include title if available
            if doc.get("title"):
                text_parts.append(doc["title"])

            # For PubMed articles, prioritize abstract
            if doc.get("source_type") == "pubmed_article":
                if doc.get("abstract"):
                    text_parts.append(doc["abstract"])
                if doc.get("mesh_terms"):
                    text_parts.append("Medical terms: " + " ".join(doc["mesh_terms"]))

            # For WHO guidelines, use body content
            elif doc.get("source_type") == "who_guideline":
                if doc.get("body"):
                    # Truncate very long WHO guideline bodies to first 2000 chars for better embedding
                    body = doc["body"]
                    if len(body) > 2000:
                        body = body[:2000] + "..."
                    text_parts.append(body)

            # Fallback to content field
            else:
                if doc.get("content"):
                    text_parts.append(doc["content"])

            full_text = " ".join(text_parts)
            # Clean up text - remove excessive whitespace
            full_text = " ".join(full_text.split())
            texts.append(full_text)

        # Generate embeddings
        try:
            embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=32)
            self.embeddings = embeddings

            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(
                dimension
            )  # Inner product for cosine similarity

            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)

            logger.info(f"Created index with {self.index.ntotal} documents")

            # Save index and metadata
            self._save_index()

        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")

    def _save_index(self):
        """Save FAISS index and document metadata to disk."""
        try:
            import faiss

            # Save FAISS index
            faiss.write_index(self.index, str(FAISS_INDEX_PATH))

            # Save document metadata
            with open(DOCUMENTS_METADATA_PATH, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)

            logger.info("Saved index and metadata to disk")

        except Exception as e:
            logger.error(f"Error saving index: {e}")

    def _load_index(self) -> bool:
        """Load FAISS index and document metadata from disk.

        Returns:
            True if successful, False otherwise
        """
        try:
            import faiss

            if not FAISS_INDEX_PATH.exists() or not DOCUMENTS_METADATA_PATH.exists():
                return False

            # Load FAISS index
            self.index = faiss.read_index(str(FAISS_INDEX_PATH))

            # Load document metadata
            with open(DOCUMENTS_METADATA_PATH, "r", encoding="utf-8") as f:
                self.documents = json.load(f)

            logger.info(f"Loaded index with {len(self.documents)} documents from disk")
            return True

        except Exception as e:
            logger.error(f"Error loading index from disk: {e}")
            return False

    def search(self, query: str, k: int = None) -> List[Dict]:
        """Search for relevant documents with enhanced medical relevance scoring.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of relevant documents with scores
        """
        if not self.model or not self.index:
            logger.error("Model or index not loaded. Call load_processed_data() first.")
            return []

        k = k or VECTOR_SEARCH_TOP_K

        try:
            # Encode query
            query_embedding = self.model.encode([query])

            import faiss

            faiss.normalize_L2(query_embedding)

            # Get more results for re-ranking
            extended_k = min(k * 3, len(self.documents))
            scores, indices = self.index.search(query_embedding, extended_k)

            results = []
            query_terms = set(query.lower().split())

            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()

                    # Calculate enhanced relevance score
                    enhanced_score = self._calculate_medical_relevance(
                        doc, query_terms, float(score)
                    )

                    doc["relevance_score"] = enhanced_score
                    doc["rank"] = i + 1
                    results.append(doc)

            # Re-rank based on enhanced scores
            results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
            return results[:k]

        except Exception as e:
            logger.error(f"Error during enhanced search: {e}")
            return []

    def _calculate_medical_relevance(
        self, doc: Dict, query_terms: set, base_score: float
    ) -> float:
        """Calculate enhanced medical relevance score."""
        score = base_score

        # Medical term overlap bonus
        content_terms = set(doc.get("content", "").lower().split())
        mesh_terms = set([term.lower() for term in doc.get("mesh_terms", [])])

        term_overlap = (
            len(query_terms.intersection(content_terms)) / len(query_terms)
            if query_terms
            else 0
        )
        mesh_overlap = (
            len(query_terms.intersection(mesh_terms)) / len(query_terms)
            if query_terms
            else 0
        )

        score += term_overlap * 0.2
        score += mesh_overlap * 0.3

        # Section priority bonus
        section_priority = doc.get("section_priority", 1)
        score += (section_priority / 5) * 0.1

        # Publication recency bonus (for PubMed articles)
        if doc.get("source_type") == "pubmed_article":
            pub_year = doc.get("publication_year", 2000)
            current_year = 2024
            if pub_year > 0:
                recency_score = max(0, (pub_year - 2000) / (current_year - 2000))
                score += recency_score * 0.1

        # Temporal relevance weighting
        temporal_weight = self._calculate_temporal_relevance(doc)
        score *= temporal_weight

        return score

    def _calculate_temporal_relevance(self, doc: Dict) -> float:
        """Calculate temporal relevance for medical documents."""
        current_year = 2024

        # Different decay rates for different types of medical information
        decay_rates = {
            "drug_safety": 0.9,  # Recent safety data is crucial
            "guidelines": 0.7,  # Guidelines change moderately
            "mechanisms": 0.3,  # Mechanisms are relatively stable
            "case_studies": 0.8,  # Recent cases are more relevant
        }

        pub_year = doc.get("publication_year", 2000)
        doc_type = self._classify_document_type(doc)
        decay_rate = decay_rates.get(doc_type, 0.5)

        if pub_year > 0:
            years_old = current_year - pub_year
            temporal_weight = max(0.1, 1 - (years_old * decay_rate / 20))
        else:
            temporal_weight = 0.5  # Default for unknown publication year

        return temporal_weight

    def _classify_document_type(self, doc: Dict) -> str:
        """Classify document type for temporal weighting."""
        title = doc.get("title", "").lower()
        content = doc.get("content", "").lower()

        if any(term in title + content for term in ["adverse", "safety", "warning"]):
            return "drug_safety"
        elif any(term in title + content for term in ["guideline", "recommendation"]):
            return "guidelines"
        elif any(
            term in title + content for term in ["mechanism", "pathway", "target"]
        ):
            return "mechanisms"
        elif any(term in title + content for term in ["case", "patient", "report"]):
            return "case_studies"

        return "general"

    def search_by_medications(
        self, medications: List[str], k: int = None
    ) -> List[Dict]:
        """Search for documents relevant to specific medications with medical ontology expansion.

        Args:
            medications: List of medication names
            k: Number of results to return

        Returns:
            List of relevant documents
        """
        query_parts = []

        for med in medications:
            # Add original medication name
            query_parts.append(med)

            # Add pharmacological class expansion
            pharm_class = self.knowledge_graph.get_pharmacological_class(med)
            if pharm_class:
                query_parts.extend(pharm_class)

            # Add therapeutic indication terms
            indications = self.knowledge_graph.get_therapeutic_indications(med)
            if indications:
                query_parts.extend(indications)

        # Add medical context terms with weights
        medical_terms = [
            "medication",
            "treatment",
            "dosage",
            "side effects",
            "contraindications",
            "drug interaction",
            "pharmacology",
            "therapeutic monitoring",
            "adverse events",
            "efficacy",
        ]
        query_parts.extend(medical_terms)

        query = " ".join(query_parts)
        return self.search(query, k)

    def enhanced_medical_search(
        self,
        query: str,
        medications: List[str] = None,
        patient_info: Dict = None,
        k: int = None,
    ) -> List[Dict]:
        """Multi-stage retrieval with medical query refinement."""
        k = k or VECTOR_SEARCH_TOP_K

        # Stage 1: Initial broad search
        initial_results = self.search(query, k * 2)

        # Stage 2: Medical relevance filtering
        filtered_results = self._filter_medical_relevance(initial_results, medications)

        # Stage 3: Query expansion based on findings
        if len(filtered_results) < k:
            expanded_query = self._expand_query_from_results(query, filtered_results)
            additional_results = self.search(expanded_query, k)
            filtered_results.extend(additional_results)

        # Stage 4: Diversity-aware re-ranking
        diverse_results = self._ensure_result_diversity(filtered_results)

        # Stage 5: Final medical scoring with patient context
        final_results = self._apply_final_medical_scoring(
            diverse_results, medications, patient_info
        )

        return final_results[:k]

    def _filter_medical_relevance(
        self, results: List[Dict], medications: List[str]
    ) -> List[Dict]:
        """Filter results for medical relevance."""
        if not medications:
            return results

        relevant_results = []
        med_terms = set([med.lower() for med in medications])

        for result in results:
            content = result.get("content", "").lower()
            mesh_terms = set([term.lower() for term in result.get("mesh_terms", [])])

            # Check for medication mentions or related terms
            if any(med in content for med in med_terms) or mesh_terms.intersection(
                med_terms
            ):
                relevant_results.append(result)

        return relevant_results

    def _expand_query_from_results(
        self, original_query: str, results: List[Dict]
    ) -> str:
        """Expand query based on initial search results."""
        # Extract additional terms from high-scoring results
        additional_terms = set()

        for result in results[:3]:  # Use top 3 results
            mesh_terms = result.get("mesh_terms", [])
            additional_terms.update([term.lower() for term in mesh_terms[:5]])

        # Combine original query with additional terms
        expanded_terms = original_query.split() + list(additional_terms)
        return " ".join(expanded_terms)

    def _ensure_result_diversity(self, results: List[Dict]) -> List[Dict]:
        """Ensure diversity in search results."""
        diverse_results = []
        seen_sources = set()

        # First pass: one result per unique source
        for result in results:
            source = result.get("source", "")
            if source not in seen_sources:
                diverse_results.append(result)
                seen_sources.add(source)

        # Second pass: add remaining high-scoring results
        for result in results:
            if result not in diverse_results and len(diverse_results) < len(results):
                diverse_results.append(result)

        return diverse_results

    def _apply_final_medical_scoring(
        self, results: List[Dict], medications: List[str], patient_info: Dict
    ) -> List[Dict]:
        """Apply final medical scoring with patient context."""
        if not patient_info:
            return results

        for result in results:
            # Apply patient-specific relevance
            patient_relevance = self._calculate_patient_relevance(result, patient_info)

            # Combine with existing relevance score
            existing_score = result.get("relevance_score", 0.5)
            result["relevance_score"] = existing_score * patient_relevance

        # Sort by final score
        return sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True)

    def search_with_patient_context(
        self, query: str, patient_info: Dict, k: int = None
    ) -> List[Dict]:
        """Search with patient-specific contextual filtering."""
        # Perform initial search
        initial_results = self.search(query, k * 2 if k else VECTOR_SEARCH_TOP_K * 2)

        # Apply patient-specific filters
        filtered_results = []

        for result in initial_results:
            patient_relevance = self._calculate_patient_relevance(result, patient_info)

            if patient_relevance > 0.3:  # Threshold for relevance
                result["patient_relevance"] = patient_relevance
                filtered_results.append(result)

        # Sort by combined relevance
        filtered_results.sort(
            key=lambda x: x["relevance_score"] * x.get("patient_relevance", 1.0),
            reverse=True,
        )

        return filtered_results[: k or VECTOR_SEARCH_TOP_K]

    def _calculate_patient_relevance(self, doc: Dict, patient_info: Dict) -> float:
        """Calculate patient-specific relevance score."""
        relevance = 1.0
        content = doc.get("content", "").lower()

        age = patient_info.get("age", 0)
        gender = patient_info.get("gender", "O")

        # Age-specific adjustments
        if age > 65 and "elderly" in content:
            relevance += 0.3
        elif age < 18 and any(term in content for term in ["pediatric", "children"]):
            relevance += 0.3
        elif 18 <= age <= 65 and "adult" in content:
            relevance += 0.1

        # Gender-specific adjustments
        if gender == "F" and any(
            term in content for term in ["women", "female", "pregnancy"]
        ):
            relevance += 0.2
        elif gender == "M" and any(term in content for term in ["men", "male"]):
            relevance += 0.2

        return min(2.0, relevance)  # Cap at 2.0

    def search_by_condition(self, condition: str, k: int = None) -> List[Dict]:
        query = f"{condition} treatment management therapy medication guidelines"
        return self.search(query, k)

    def search_by_medical_condition(
        self, condition: str, symptoms: List[str] = None, k: int = None
    ) -> List[Dict]:
        query_parts = [condition]

        if symptoms:
            query_parts.extend(symptoms)

        # Add general medical terms
        query_parts.extend(
            [
                "treatment",
                "management",
                "therapy",
                "diagnosis",
                "clinical",
                "patient",
                "symptoms",
                "prevention",
            ]
        )

        query = " ".join(query_parts)
        return self.search(query, k)

    def search_by_symptoms(self, symptoms: List[str], k: int = None) -> List[Dict]:
        """Search for documents based on symptoms.

        Args:
            symptoms: List of symptoms
            k: Number of results to return

        Returns:
            List of relevant documents
        """
        query_parts = symptoms.copy()
        query_parts.extend(
            [
                "symptoms",
                "diagnosis",
                "clinical",
                "manifestation",
                "signs",
                "presentation",
                "condition",
                "disease",
            ]
        )

        query = " ".join(query_parts)
        return self.search(query, k)

    def search_by_treatment(self, treatment_type: str, k: int = None) -> List[Dict]:
        """Search for documents related to specific treatments.

        Args:
            treatment_type: Type of treatment
            k: Number of results to return

        Returns:
            List of relevant documents
        """
        query = f"{treatment_type} treatment therapy intervention protocol management clinical guidelines"
        return self.search(query, k)

    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        for doc in self.documents:
            if doc.get("id") == doc_id:
                return doc
        return None

    def get_stats(self) -> Dict:
        stats = {
            "total_documents": len(self.documents),
            "model_name": self.model_name,
            "index_loaded": self.index is not None,
            "embedding_dimension": self.embeddings.shape[1]
            if self.embeddings is not None
            else 0,
        }

        if self.documents:
            source_types = {}
            for doc in self.documents:
                source_type = doc.get("source_type", "unknown")
                source_types[source_type] = source_types.get(source_type, 0) + 1
            stats["source_types"] = source_types

        return stats
