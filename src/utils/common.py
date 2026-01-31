"""Common utility functions for the medical guideline RAG system.

This module provides shared utilities to reduce code duplication across
the codebase. Functions include JSON I/O, HTTP session creation, and
date/time helpers.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests


def get_current_year() -> int:
    """Get the current year.
    
    Returns:
        The current year as an integer.
    """
    return datetime.now().year


def save_json(
    data: Union[Dict[str, Any], List[Any]],
    filepath: Union[str, Path],
    indent: int = 2,
    ensure_ascii: bool = False,
) -> None:
    """Save data to a JSON file.
    
    Args:
        data: The data to save (dict or list).
        filepath: Path to the output file.
        indent: JSON indentation level (default: 2).
        ensure_ascii: If True, escape non-ASCII characters (default: False).
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)


def load_json(filepath: Union[str, Path]) -> Union[Dict[str, Any], List[Any]]:
    """Load data from a JSON file.
    
    Args:
        filepath: Path to the JSON file.
        
    Returns:
        The loaded data (dict or list).
        
    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def create_http_session(
    timeout: int = 30,
    retries: int = 3,
    backoff_factor: float = 0.5,
    user_agent: Optional[str] = None,
) -> requests.Session:
    """Create a configured HTTP session with retry logic.
    
    Args:
        timeout: Request timeout in seconds (default: 30).
        retries: Number of retry attempts (default: 3).
        backoff_factor: Backoff factor for retries (default: 0.5).
        user_agent: Custom User-Agent string (optional).
        
    Returns:
        A configured requests.Session object.
    """
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    session = requests.Session()
    
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST"],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    if user_agent:
        session.headers.update({"User-Agent": user_agent})
    
    return session


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks.
    
    Args:
        text: The text to chunk.
        chunk_size: Maximum size of each chunk (default: 1000).
        overlap: Number of characters to overlap between chunks (default: 100).
        
    Returns:
        List of text chunks.
    """
    if not text or chunk_size <= 0:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        
        if start >= text_length:
            break
    
    return chunks
