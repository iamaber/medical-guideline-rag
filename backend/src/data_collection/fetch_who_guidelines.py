import os
import json
import uuid
from collections import defaultdict

from src.preprocessing.pdf_to_text import process_pdf_to_chunks
from src.preprocessing.clean_text import nlp_preprocessing
from src.preprocessing.summarizer import summarizer

RAW_PDF_DIR = "data/raw/"
PROCESSED_JSON_DIR = "data/processed"


def fetch_who_guidelines() -> None:
    if not os.path.exists(RAW_PDF_DIR):
        print(f"ERROR: Directory {RAW_PDF_DIR} does not exist!")
        return

    all_files = os.listdir(RAW_PDF_DIR)
    pdf_files = [f for f in all_files if f.endswith(".pdf")]

    os.makedirs(PROCESSED_JSON_DIR, exist_ok=True)
    print(f"Created/verified output directory: {os.path.abspath(PROCESSED_JSON_DIR)}")

    docs_by_title = defaultdict(list)
    for filename in pdf_files:
        pdf_path = os.path.join(RAW_PDF_DIR, filename)
        try:
            chunks = process_pdf_to_chunks(pdf_path)
            print(f"Extracted {len(chunks)} chunks from {filename}")

            for chunk in chunks:
                if chunk.strip():
                    cleaned_chunk = nlp_preprocessing(chunk)
                    title = filename.replace(".pdf", "")
                    docs_by_title[title].append(cleaned_chunk)
        except Exception as e:
            print(f"ERROR processing {filename}: {str(e)}")
            continue

    all_docs = []
    for title, chunks in docs_by_title.items():
        doc_id = str(uuid.uuid4())
        document = {
            "id": doc_id,
            "title": title,
            "body": summarizer("\n".join(chunks)),
            "source": f"WHO Guidelines: {title}.pdf",
        }
        all_docs.append(document)

    if all_docs:
        output_path = os.path.join(PROCESSED_JSON_DIR, "who_guidelines.json")
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_docs, f, indent=4, ensure_ascii=False)
            print(f"Successfully saved {len(all_docs)} documents to {output_path}")
        except Exception as e:
            print(f"ERROR saving JSON file: {str(e)}")
    else:
        print("No documents to save - no JSON file created")


if __name__ == "__main__":
    fetch_who_guidelines()
