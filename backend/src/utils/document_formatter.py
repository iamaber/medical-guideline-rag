"""Document formatting utilities for vector search.

This module handles the formatting of different document types
(PubMed articles, WHO guidelines, etc.) for vector indexing.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DocumentFormatter:
    """Formats documents for vector search indexing.

    Handles different document formats and extracts structured data
    for enhanced search capabilities.
    """

    def format_document(self, item: Dict[str, Any], source_file: str) -> Optional[List[Dict[str, Any]]]:
        """Format a document for indexing with medical section awareness.

        Args:
            item: Raw document data.
            source_file: Name of the source file.

        Returns:
            List of formatted documents or None if invalid.
        """
        if "pmid" in item:
            return self._format_pubmed_article(item, source_file)
        elif "id" in item and "body" in item:
            return [self._format_who_guideline(item, source_file)]
        else:
            result = self._format_generic_document(item, source_file)
            return [result] if result else None

    def _format_pubmed_article(self, item: Dict[str, Any], source_file: str) -> List[Dict[str, Any]]:
        """Format a PubMed article with section extraction.

        Args:
            item: PubMed article data.
            source_file: Name of the source file.

        Returns:
            List of formatted document sections.
        """
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

        return formatted_docs if formatted_docs else []

    def _format_who_guideline(self, item: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """Format a WHO guideline document.

        Args:
            item: WHO guideline data.
            source_file: Name of the source file.

        Returns:
            Formatted document dictionary.
        """
        title = item.get("title", "")
        body = item.get("body", "")
        text_content = f"{title}. {body}" if title and body else (title or body)

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

    def _format_generic_document(self, item: Dict[str, Any], source_file: str) -> Optional[Dict[str, Any]]:
        """Format a generic document with fallback field detection.

        Args:
            item: Generic document data.
            source_file: Name of the source file.

        Returns:
            Formatted document or None if no content found.
        """
        content_fields = ["title", "abstract", "body", "content", "text", "description"]
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

    def _extract_medical_sections(self, item: Dict[str, Any]) -> Dict[str, str]:
        """Extract medical sections from a document.

        Args:
            item: Document with potential section data.

        Returns:
            Dictionary mapping section types to content.
        """
        sections = {}
        title = item.get("title", "")
        abstract = item.get("abstract", "")

        sections["title"] = title
        sections["abstract"] = abstract

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
        """Extract a specific section from text.

        Args:
            text: Full text to search.
            section_type: Type of section to extract.

        Returns:
            Extracted section content or empty string.
        """
        text_lower = text.lower()
        section_keywords = {
            "methods": ["methods", "methodology", "design", "participants"],
            "results": ["results", "findings", "outcomes", "data"],
            "conclusion": ["conclusion", "conclusions", "summary", "implications"],
        }

        keywords = section_keywords.get(section_type, [])
        for keyword in keywords:
            if keyword in text_lower:
                start_idx = text_lower.find(keyword)
                if start_idx != -1:
                    sentences = text[start_idx:].split(".")
                    return ". ".join(sentences[:2]) + "." if len(sentences) > 1 else sentences[0]

        return ""

    def _get_section_priority(self, section_type: str) -> int:
        """Assign priority scores to different medical sections.

        Args:
            section_type: Type of section.

        Returns:
            Priority score (higher = more important).
        """
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


class MedicalRelevanceScorer:
    """Calculates medical relevance scores for search results."""

    def __init__(self, current_year: int = 2024):
        self.current_year = current_year

    def calculate_score(
        self,
        doc: Dict[str, Any],
        query_terms: set,
        base_score: float,
        patient_info: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate enhanced medical relevance score.

        Args:
            doc: Document to score.
            query_terms: Set of query terms.
            base_score: Base similarity score.
            patient_info: Optional patient context.

        Returns:
            Enhanced relevance score.
        """
        score = base_score

        score += self._calculate_term_overlap(doc, query_terms)
        score += self._calculate_section_bonus(doc)
        score += self._calculate_recency_bonus(doc)
        score *= self._calculate_temporal_weight(doc)

        if patient_info:
            score *= self._calculate_patient_relevance(doc, patient_info)

        return score

    def _calculate_term_overlap(self, doc: Dict[str, Any], query_terms: set) -> float:
        """Calculate term overlap bonus."""
        content_terms = set(doc.get("content", "").lower().split())
        mesh_terms = set(term.lower() for term in doc.get("mesh_terms", []))

        term_overlap = (
            len(query_terms.intersection(content_terms)) / len(query_terms)
            if query_terms else 0
        )
        mesh_overlap = (
            len(query_terms.intersection(mesh_terms)) / len(query_terms)
            if query_terms else 0
        )

        return term_overlap * 0.2 + mesh_overlap * 0.3

    def _calculate_section_bonus(self, doc: Dict[str, Any]) -> float:
        """Calculate section priority bonus."""
        section_priority = doc.get("section_priority", 1)
        return (section_priority / 5) * 0.1

    def _calculate_recency_bonus(self, doc: Dict[str, Any]) -> float:
        """Calculate publication recency bonus."""
        if doc.get("source_type") != "pubmed_article":
            return 0.0

        pub_year = doc.get("publication_year", 2000)
        if pub_year > 0:
            recency_score = max(0, (pub_year - 2000) / (self.current_year - 2000))
            return recency_score * 0.1
        return 0.0

    def _calculate_temporal_weight(self, doc: Dict[str, Any]) -> float:
        """Calculate temporal relevance weight."""
        decay_rates = {
            "drug_safety": 0.9,
            "guidelines": 0.7,
            "mechanisms": 0.3,
            "case_studies": 0.8,
        }

        pub_year = doc.get("publication_year", 2000)
        doc_type = self._classify_document_type(doc)
        decay_rate = decay_rates.get(doc_type, 0.5)

        if pub_year > 0:
            years_old = self.current_year - pub_year
            return max(0.1, 1 - (years_old * decay_rate / 20))
        return 0.5

    def _classify_document_type(self, doc: Dict[str, Any]) -> str:
        """Classify document type for temporal weighting."""
        title = doc.get("title", "").lower()
        content = doc.get("content", "").lower()
        combined = title + content

        if any(term in combined for term in ["adverse", "safety", "warning"]):
            return "drug_safety"
        elif any(term in combined for term in ["guideline", "recommendation"]):
            return "guidelines"
        elif any(term in combined for term in ["mechanism", "pathway", "target"]):
            return "mechanisms"
        elif any(term in combined for term in ["case", "patient", "report"]):
            return "case_studies"
        return "general"

    def _calculate_patient_relevance(self, doc: Dict[str, Any], patient_info: Dict[str, Any]) -> float:
        """Calculate patient-specific relevance multiplier."""
        relevance = 1.0
        content = doc.get("content", "").lower()

        age = patient_info.get("age", 0)
        gender = patient_info.get("gender", "O")

        if age > 65 and "elderly" in content:
            relevance += 0.3
        elif age < 18 and any(term in content for term in ["pediatric", "children"]):
            relevance += 0.3
        elif 18 <= age <= 65 and "adult" in content:
            relevance += 0.1

        if gender == "F" and any(term in content for term in ["women", "female", "pregnancy"]):
            relevance += 0.2
        elif gender == "M" and any(term in content for term in ["men", "male"]):
            relevance += 0.2

        return min(2.0, relevance)
