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

logger = logging.getLogger(__name__)


class VectorSearch:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or EMBEDDING_MODEL
        self.model = None
        self.index = None
        self.documents = []
        self.embeddings = None
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
                                documents.append(doc)
                elif isinstance(data, dict):
                    doc = self._format_document(data, json_file.name)
                    if doc:
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
        """Format document for indexing."""
        # Handle PubMed articles format
        if "pmid" in item:
            text_content = ""
            title = item.get("title", "")
            abstract = item.get("abstract", "")
            mesh_terms = item.get("mesh_terms", [])

            # Combine title and abstract for better content
            if title and abstract:
                text_content = f"{title}. {abstract}"
            elif title:
                text_content = title
            elif abstract:
                text_content = abstract

            # Add mesh terms to content for better searchability
            if mesh_terms:
                text_content += f" Medical terms: {' '.join(mesh_terms)}"

            if not text_content:
                return None

            return {
                "id": str(item["pmid"]),
                "title": title,
                "content": text_content,
                "source": item.get("source", source_file),
                "source_type": "pubmed_article",
                "mesh_terms": mesh_terms,
                "abstract": abstract,
                "publication_date": item.get("publication_date", ""),
            }

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
                "mesh_terms": item.get("mesh_terms", []),
                "keywords": item.get("keywords", []),
            }

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
        """Search for relevant documents.

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

            # Search
            scores, indices = self.index.search(query_embedding, k)

            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc["relevance_score"] = float(score)
                    doc["rank"] = i + 1
                    results.append(doc)

            return results

        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []

    def search_by_medications(
        self, medications: List[str], k: int = None
    ) -> List[Dict]:
        """Search for documents relevant to specific medications.

        Args:
            medications: List of medication names
            k: Number of results to return

        Returns:
            List of relevant documents
        """
        # Create comprehensive query from medication names
        query_parts = []
        query_parts.extend(medications)
        query_parts.extend(
            [
                "medication",
                "treatment",
                "dosage",
                "side effects",
                "contraindications",
                "drug interaction",
                "pharmacology",
            ]
        )

        query = " ".join(query_parts)
        return self.search(query, k)

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
