import json
import os
import time
from Bio import Entrez
from config.settings import NCBI_EMAIL, NCBI_API_KEY
from src.preprocessing.clean_text import nlp_preprocessing

Entrez.email = NCBI_EMAIL
Entrez.api_key = NCBI_API_KEY

# Define search queries grouped by disease/topic
SEARCH_QUERIES = {
    "dengue": [
        "Dengue AND Bangladesh",
        "Dengue AND (Treatment OR Guidelines)",
    ],
    "typhoid": [
        "Typhoid Fever AND Bangladesh",
        "Typhoid Fever AND (Treatment OR Management)",
    ],
    "malaria": [
        "Malaria AND Bangladesh",
        "Malaria AND (Treatment OR Prevention)",
    ],
    "hepatitis": [
        "Hepatitis AND Bangladesh",
        "Hepatitis AND (Treatment OR Management)",
    ],
    "diarrhea": [
        "Diarrhea AND Bangladesh",
        "Diarrhea AND (Treatment OR Guidelines)",
    ],
    "tuberculosis": [
        "Tuberculosis AND Bangladesh",
        "Tuberculosis AND (Treatment OR WHO Guidelines)",
    ],
    "cholera": [
        "Cholera AND Bangladesh",
        "Cholera AND (Management OR Treatment)",
    ],
    "leptospirosis": [
        "Leptospirosis AND Bangladesh",
        "Leptospirosis AND Treatment",
    ],
    "leishmaniasis": [
        "Leishmaniasis AND Bangladesh",
        "Leishmaniasis AND Treatment",
    ],
    "influenza": [
        "Influenza AND Bangladesh",
        "Influenza AND Treatment",
    ],
    "diabetes": [
        "Diabetes AND Bangladesh",
        "Diabetes AND (Management OR Treatment)",
    ],
    "hypertension": [
        "Hypertension AND Bangladesh",
        "Hypertension AND Guidelines",
    ],
    "cardiovascular": [
        "Cardiovascular Diseases AND Bangladesh",
        "Cardiovascular Diseases AND Treatment",
    ],
    "ckd": [
        "Chronic Kidney Disease AND Bangladesh",
        "Chronic Kidney Disease AND Management",
    ],
    "cancer": [
        "Cancer AND Bangladesh",
        "Cancer AND (Treatment OR Management)",
    ],
    "maternal_health": [
        "Maternal Health AND Bangladesh",
        "Maternal Health AND Guidelines",
    ],
    "neonatal_care": [
        "Neonatal Care AND Bangladesh",
        "Neonatal Care AND WHO Guidelines",
    ],
    "malnutrition": [
        "Malnutrition AND Bangladesh",
        "Malnutrition AND Treatment",
    ],
    "immunization": [
        "Vaccination AND Bangladesh",
        "Immunization AND WHO Guidelines",
    ],
    "surveillance": [
        "Disease Surveillance AND Bangladesh",
        "Disease Surveillance AND WHO",
    ],
    "outbreak_management": [
        "Outbreak Response AND Bangladesh",
        "Outbreak Response AND Guidelines",
    ],
    "health_policy": [
        "Health Policy AND Bangladesh",
        "Health Policy AND Guidelines",
    ],
    "amr": [
        "Antibiotic Resistance AND Bangladesh",
        "Antimicrobial Resistance AND WHO Guidelines",
    ],
    "essential_medicines": [
        "Essential Medicines AND Bangladesh",
        "Essential Medicines AND WHO Guidelines",
    ],
    "drug_pricing": [
        "Drug Pricing AND Bangladesh",
        "Drug Pricing AND Policies",
    ],
    "healthcare_system": ["Healthcare System AND Bangladesh"],
    "primary_healthcare": ["Primary Healthcare AND Bangladesh"],
    "rural_health_services": ["Rural Health Services AND Bangladesh"],
    "community_health_workers": ["Community Health Workers AND Bangladesh"],
    "infectious_diseases": ["Infectious Diseases AND Bangladesh"],
    "ncd": ["Non-communicable Diseases AND Bangladesh"],
    "public_health_guidelines": ["Public Health Guidelines AND Bangladesh"],
    "disease_surveillance_reports": ["Bangladesh Disease Surveillance Reports"],
}


def fetch_pubmed_id(query: str, max_results: int = 100) -> list:
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]


def fetch_pubmed_abstracts(id_list: list, batch_size: int = 20) -> list:
    abstracts = []
    for start in range(0, len(id_list), batch_size):
        batch_ids = id_list[start : start + batch_size]
        ids = ",".join(batch_ids)
        handle = Entrez.efetch(db="pubmed", id=ids, rettype="abstract", retmode="xml")
        records = Entrez.read(handle)
        handle.close()

        for article in records["PubmedArticle"]:
            article_data = article["MedlineCitation"]["Article"]
            title = article_data.get("ArticleTitle", "No Title")
            abstract_data = article_data.get("Abstract", {}).get("AbstractText", "")
            if isinstance(abstract_data, list):
                abstract_text = " ".join([str(a) for a in abstract_data])
            elif isinstance(abstract_data, str):
                abstract_text = abstract_data
            else:
                abstract_text = ""
            # clean abstract text
            abstract_text = nlp_preprocessing(abstract_text)

            pmid = article["MedlineCitation"]["PMID"]
            mesh_terms = [
                mesh["DescriptorName"]
                for mesh in article["MedlineCitation"].get("MeshHeadingList", [])
            ]

            article_info = {
                "pmid": str(pmid),
                "title": str(title),
                "abstract": str(abstract_text),
                "mesh_terms": mesh_terms,
                "source": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
            abstracts.append(article_info)

        time.sleep(0.3)

    return abstracts


def save_to_json(data: list, output_file: str) -> None:
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def fetch_and_save_pubmed_abstracts(max_results: int = 100) -> None:
    for topic, queries in SEARCH_QUERIES.items():
        all_abstracts = []
        all_ids = set()  # Use set to avoid duplicates

        for query in queries:
            ids = fetch_pubmed_id(query, max_results=max_results)
            print(f"Found {len(ids)} articles for query '{query}'.")

            # Filter out duplicate IDs
            new_ids = [id for id in ids if id not in all_ids]
            all_ids.update(new_ids)

            if new_ids:
                abstracts = fetch_pubmed_abstracts(new_ids)
                all_abstracts.extend(abstracts)

        output_file = f"data/processed/{topic}.json"
        save_to_json(all_abstracts, output_file)
        print(f"Saved {len(all_abstracts)} total articles to {output_file}")


if __name__ == "__main__":
    fetch_and_save_pubmed_abstracts(max_results=100)
