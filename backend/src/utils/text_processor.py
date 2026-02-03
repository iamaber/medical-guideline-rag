"""Text processing utilities for cleaning and normalizing medical text."""

import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TextProcessor:
    """Text processing utilities for medical content."""

    def __init__(self):
        """Initialize the text processor."""
        self.nlp = None
        self._load_spacy_model()

    def _load_spacy_model(self):
        """Load spaCy model with error handling."""
        try:
            import spacy

            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except ImportError:
            logger.warning("spaCy not installed. Some features will be limited.")
        except OSError:
            logger.warning(
                "spaCy model not found. Install with: python -m spacy download en_core_web_sm"
            )
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Remove citations and references
        text = re.sub(r"\[\d+\]", "", text)
        text = re.sub(r"\(\d+\)", "", text)
        text = re.sub(r"et al\.", "", text)

        # Remove URLs
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )

        # Clean up medical dosage patterns
        text = re.sub(r"\d+\s*mg/kg", "DOSAGE_MG_KG", text)
        text = re.sub(r"\d+\s*mg", "DOSAGE_MG", text)
        text = re.sub(r"\d+\s*ml", "DOSAGE_ML", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters but keep medical terms
        text = re.sub(r"[^\w\s\-\+\.\,\:\;\(\)]", "", text)

        return text.strip()

    def extract_medical_terms(self, text: str) -> List[str]:
        """Extract medical terms and drug names from text.

        Args:
            text: Text to extract terms from

        Returns:
            List of medical terms
        """
        if not self.nlp or not text:
            return []

        try:
            doc = self.nlp(text)
            medical_terms = []

            for ent in doc.ents:
                # Extract entities that might be medical terms
                if ent.label_ in ["PERSON", "ORG", "PRODUCT", "GPE"]:
                    if len(ent.text) > 2 and ent.text.isalpha():
                        medical_terms.append(ent.text)

            # Extract potential drug names (capitalized words)
            for token in doc:
                if (
                    token.is_alpha
                    and token.text[0].isupper()
                    and len(token.text) > 3
                    and not token.is_stop
                ):
                    medical_terms.append(token.text)

            return list(set(medical_terms))

        except Exception as e:
            logger.error(f"Error extracting medical terms: {e}")
            return []

    def lemmatize_text(self, text: str) -> str:
        """Lemmatize text while preserving medical terms.

        Args:
            text: Text to lemmatize

        Returns:
            Lemmatized text
        """
        if not self.nlp or not text:
            return text

        try:
            doc = self.nlp(text)
            lemmatized = []

            for token in doc:
                if token.is_alpha and not token.is_stop:
                    # Preserve medical terms in uppercase
                    if token.text[0].isupper() and len(token.text) > 3:
                        lemmatized.append(token.text)
                    else:
                        lemmatized.append(token.lemma_.lower())
                elif not token.is_space:
                    lemmatized.append(token.text)

            return " ".join(lemmatized)

        except Exception as e:
            logger.error(f"Error lemmatizing text: {e}")
            return text

    def extract_dosage_info(self, text: str) -> Dict[str, List[str]]:
        """Extract dosage information from text.

        Args:
            text: Text containing dosage information

        Returns:
            Dictionary with dosage patterns
        """
        dosage_patterns = {
            "mg_doses": [],
            "ml_doses": [],
            "frequency": [],
            "duration": [],
        }

        # Extract mg doses
        mg_matches = re.findall(r"(\d+(?:\.\d+)?)\s*mg", text, re.IGNORECASE)
        dosage_patterns["mg_doses"] = mg_matches

        # Extract ml doses
        ml_matches = re.findall(r"(\d+(?:\.\d+)?)\s*ml", text, re.IGNORECASE)
        dosage_patterns["ml_doses"] = ml_matches

        # Extract frequency patterns
        freq_matches = re.findall(
            r"(once|twice|three times|four times|daily|weekly|monthly)",
            text,
            re.IGNORECASE,
        )
        dosage_patterns["frequency"] = freq_matches

        # Extract duration patterns
        duration_matches = re.findall(
            r"for\s+(\d+)\s+(days?|weeks?|months?)", text, re.IGNORECASE
        )
        dosage_patterns["duration"] = [
            f"{num} {unit}" for num, unit in duration_matches
        ]

        return dosage_patterns

    def normalize_medication_name(self, med_name: str) -> str:
        """Normalize medication name for consistent lookup.

        Args:
            med_name: Raw medication name

        Returns:
            Normalized medication name
        """
        if not med_name:
            return ""

        # Remove extra spaces and normalize case
        normalized = " ".join(med_name.split()).title()

        # Remove common suffixes that might interfere with lookup
        suffixes_to_remove = [
            "Tablet",
            "Capsule",
            "Syrup",
            "Injection",
            "Cream",
            "Ointment",
        ]
        for suffix in suffixes_to_remove:
            if normalized.endswith(f" {suffix}"):
                normalized = normalized[: -len(f" {suffix}")]

        return normalized.strip()
