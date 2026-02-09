"""Vector search service for medical literature retrieval.

This module provides semantic search capabilities using FAISS and
sentence transformers for medical document retrieval.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import Defaults, Paths, get_settings
from src.utils.document_formatter import DocumentFormatter, MedicalRelevanceScorer
from src.services.medical_knowledge_graph import MedicalKnowledgeGraph

logger = logging.getLogger(__name__)


class VectorSearch:
    """Semantic search service using FAISS and sentence transformers.

    Provides medical literature retrieval with enhanced relevance scoring
    and patient-specific context awareness.
    """

    def __init__(self, model_name: Optional[str] = None) -> None:
        """Initialize the vector search service.

        Args:
            model_name: Optional embedding model name. Uses default if not provided.
        """
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.knowledge_graph = MedicalKnowledgeGraph()
        self.formatter = DocumentFormatter()
        self.scorer = MedicalRelevanceScorer()
        self._query_embedding_cache: Dict[str, np.ndarray] = {}
        self._cache_max_size = 1000
        self._load_model()

    def _load_model(self) -> None:
        """Load the sentence transformer embedding model."""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded sentence transformer model: {self.model_name}")
        except ImportError:
            logger.error("sentence-transformers not installed")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")

    def _get_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """Get embedding for a query, using cache if available.

        Args:
            query: The query text to encode.

        Returns:
            Normalized embedding array for the query.
        """
        if self.model is None:
            return None

        if query in self._query_embedding_cache:
            return self._query_embedding_cache[query]

        embedding = self.model.encode([query])
        faiss.normalize_L2(embedding)

        if len(self._query_embedding_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._query_embedding_cache))
            del self._query_embedding_cache[oldest_key]

        self._query_embedding_cache[query] = embedding
        return embedding

    def clear_embedding_cache(self) -> None:
        """Clear the query embedding cache."""
        self._query_embedding_cache.clear()
        logger.info("Query embedding cache cleared")

    def load_processed_data(self, data_dir: Optional[str] = None) -> None:
        """Load and process documents from the data directory.

        Args:
            data_dir: Optional path to data directory.
        """
        if self.model is None:
            logger.error("Model not loaded. Cannot process documents.")
            return

        data_path = Path(data_dir) if data_dir else Paths.PROCESSED_DIR
        documents: List[Dict[str, Any]] = []

        logger.info(f"Loading documents from: {data_path}")

        json_files = list(data_path.glob("*.json"))
        if not json_files:
            logger.warning(f"No JSON files found in {data_path}")
            return

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict):
                        formatted = self.formatter.format_document(item, json_file.name)
                        if formatted:
                            documents.extend(formatted)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        self.documents = documents
        logger.info(f"Loaded {len(documents)} documents")

        if documents:
            self._create_index()
        else:
            logger.warning("No documents loaded for indexing")

    def _create_index(self) -> None:
        """Create FAISS index from documents."""
        if self.model is None:
            logger.error("Model not loaded")
            return

        logger.info("Creating vector embeddings...")

        texts = self._prepare_texts_for_embedding()
        if not texts:
            logger.warning("No texts to embed")
            return

        try:
            self.embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=32)

            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            faiss.normalize_L2(self.embeddings)
            self.index.add(self.embeddings)

            logger.info(f"Created index with {self.index.ntotal} documents")
            self._save_index()

        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")

    def _prepare_texts_for_embedding(self) -> List[str]:
        """Prepare document texts for embedding."""
        texts = []
        for doc in self.documents:
            text_parts = []

            if doc.get("title"):
                text_parts.append(doc["title"])

            if doc.get("source_type") == "pubmed_article":
                if doc.get("abstract"):
                    text_parts.append(doc["abstract"])
                if doc.get("mesh_terms"):
                    text_parts.append("Medical terms: " + " ".join(doc["mesh_terms"]))
            elif doc.get("source_type") == "who_guideline":
                body = doc.get("body", "")
                if len(body) > 2000:
                    body = body[:2000] + "..."
                text_parts.append(body)
            else:
                if doc.get("content"):
                    text_parts.append(doc["content"])

            full_text = " ".join(text_parts)
            full_text = " ".join(full_text.split())
            texts.append(full_text)

        return texts

    def _save_index(self) -> None:
        """Save FAISS index and document metadata to disk."""
        try:
            faiss.write_index(self.index, str(Paths.FAISS_INDEX_PATH))

            with open(Paths.DOCUMENTS_METADATA_PATH, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)

            logger.info("Saved index and metadata to disk")

        except Exception as e:
            logger.error(f"Error saving index: {e}")

    def _load_index(self) -> bool:
        """Load FAISS index and document metadata from disk.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if not Paths.FAISS_INDEX_PATH.exists() or not Paths.DOCUMENTS_METADATA_PATH.exists():
                return False

            self.index = faiss.read_index(str(Paths.FAISS_INDEX_PATH))

            with open(Paths.DOCUMENTS_METADATA_PATH, "r", encoding="utf-8") as f:
                self.documents = json.load(f)

            logger.info(f"Loaded index with {len(self.documents)} documents from disk")
            return True

        except Exception as e:
            logger.error(f"Error loading index from disk: {e}")
            return False

    def search(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for relevant documents.

        Args:
            query: Search query string.
            k: Number of results to return.

        Returns:
            List of relevant documents with scores.
        """
        if self.model is None or self.index is None:
            logger.error("Model or index not loaded")
            return []

        k = k or get_settings().vector_search_top_k

        try:
            query_embedding = self._get_query_embedding(query)
            if query_embedding is None:
                return []

            extended_k = min(k * 3, len(self.documents))
            scores, indices = self.index.search(query_embedding, extended_k)

            results = []
            query_terms = set(query.lower().split())

            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    enhanced_score = self.scorer.calculate_score(doc, query_terms, float(score))
                    doc["relevance_score"] = enhanced_score
                    doc["rank"] = i + 1
                    results.append(doc)

            results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
            return results[:k]

        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []

    def search_by_medications(
        self, medications: List[str], k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for documents relevant to specific medications.

        Args:
            medications: List of medication names.
            k: Number of results to return.

        Returns:
            List of relevant documents.
        """
        query_parts = []

        for med in medications:
            query_parts.append(med)

            pharm_class = self.knowledge_graph.get_pharmacological_class(med)
            if pharm_class:
                query_parts.extend(pharm_class)

            indications = self.knowledge_graph.get_therapeutic_indications(med)
            if indications:
                query_parts.extend(indications)

        medical_terms = [
            "medication", "treatment", "dosage", "side effects",
            "contraindications", "drug interaction", "pharmacology",
            "therapeutic monitoring", "adverse events", "efficacy",
        ]
        query_parts.extend(medical_terms)

        query = " ".join(query_parts)
        return self.search(query, k)

    def enhanced_medical_search(
        self,
        query: str,
        medications: Optional[List[str]] = None,
        patient_info: Optional[Dict[str, Any]] = None,
        k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Multi-stage retrieval with medical query refinement.

        Args:
            query: Search query.
            medications: Optional list of medications.
            patient_info: Optional patient context.
            k: Number of results to return.

        Returns:
            List of relevant documents.
        """
        settings = get_settings()
        k = k or settings.vector_search_top_k

        initial_results = self.search(query, k * 2)

        if medications:
            initial_results = self._filter_medical_relevance(initial_results, medications)

        if len(initial_results) < k:
            expanded_query = self._expand_query_from_results(query, initial_results)
            additional_results = self.search(expanded_query, k)
            initial_results.extend(additional_results)

        diverse_results = self._ensure_result_diversity(initial_results)

        if patient_info:
            for result in diverse_results:
                patient_relevance = self.scorer._calculate_patient_relevance(result, patient_info)
                existing_score = result.get("relevance_score", 0.5)
                result["relevance_score"] = existing_score * patient_relevance
            diverse_results = sorted(diverse_results, key=lambda x: x.get("relevance_score", 0), reverse=True)

        return diverse_results[:k]

    def _filter_medical_relevance(
        self, results: List[Dict[str, Any]], medications: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter results for medical relevance."""
        med_terms = set(med.lower() for med in medications)
        relevant_results = []

        for result in results:
            content = result.get("content", "").lower()
            mesh_terms = set(term.lower() for term in result.get("mesh_terms", []))

            if any(med in content for med in med_terms) or mesh_terms.intersection(med_terms):
                relevant_results.append(result)

        return relevant_results

    def _expand_query_from_results(
        self, original_query: str, results: List[Dict[str, Any]]
    ) -> str:
        """Expand query based on initial search results."""
        additional_terms = set()

        for result in results[:3]:
            mesh_terms = result.get("mesh_terms", [])
            additional_terms.update(term.lower() for term in mesh_terms[:5])

        expanded_terms = original_query.split() + list(additional_terms)
        return " ".join(expanded_terms)

    def _ensure_result_diversity(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure diversity in search results."""
        diverse_results = []
        seen_sources = set()

        for result in results:
            source = result.get("source", "")
            if source not in seen_sources:
                diverse_results.append(result)
                seen_sources.add(source)

        for result in results:
            if result not in diverse_results and len(diverse_results) < len(results):
                diverse_results.append(result)

        return diverse_results

    def search_by_condition(self, condition: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for documents by medical condition.

        Args:
            condition: Medical condition name.
            k: Number of results to return.

        Returns:
            List of relevant documents.
        """
        query = f"{condition} treatment management therapy medication guidelines"
        return self.search(query, k)

    def search_by_symptoms(self, symptoms: List[str], k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for documents based on symptoms.

        Args:
            symptoms: List of symptoms.
            k: Number of results to return.

        Returns:
            List of relevant documents.
        """
        query_parts = symptoms.copy()
        query_parts.extend([
            "symptoms", "diagnosis", "clinical", "manifestation",
            "signs", "presentation", "condition", "disease",
        ])
        query = " ".join(query_parts)
        return self.search(query, k)

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by its ID.

        Args:
            doc_id: Document ID.

        Returns:
            Document dict or None if not found.
        """
        for doc in self.documents:
            if doc.get("id") == doc_id:
                return doc
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index.

        Returns:
            Dictionary with index statistics.
        """
        stats: Dict[str, Any] = {
            "total_documents": len(self.documents),
            "model_name": self.model_name,
            "index_loaded": self.index is not None,
            "embedding_dimension": self.embeddings.shape[1] if self.embeddings is not None else 0,
        }

        if self.documents:
            source_types: Dict[str, int] = {}
            for doc in self.documents:
                source_type = doc.get("source_type", "unknown")
                source_types[source_type] = source_types.get(source_type, 0) + 1
            stats["source_types"] = source_types

        return stats
