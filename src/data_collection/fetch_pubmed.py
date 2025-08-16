import json
import os
import time
from Bio import Entrez
from config.settings import NCBI_EMAIL, NCBI_API_KEY

Entrez.email = NCBI_EMAIL
Entrez.api_key = NCBI_API_KEY

# Define search queries before using them
SEARCH_QUERIES = {
    # Infectious Diseases (High Priority for Bangladesh)
    "dengue_bangladesh": "Dengue AND Bangladesh",
    "dengue_global": "Dengue AND (Treatment OR Guidelines)",
    "typhoid_bangladesh": "Typhoid Fever AND Bangladesh",
    "typhoid_global": "Typhoid Fever AND (Treatment OR Management)",
    "malaria_bangladesh": "Malaria AND Bangladesh",
    "malaria_global": "Malaria AND (Treatment OR Prevention)",
    "hepatitis_bangladesh": "Hepatitis AND Bangladesh",
    "hepatitis_global": "Hepatitis AND (Treatment OR Management)",
    "diarrhea_bangladesh": "Diarrhea AND Bangladesh",
    "diarrhea_global": "Diarrhea AND (Treatment OR Guidelines)",
    "tuberculosis_bangladesh": "Tuberculosis AND Bangladesh",
    "tuberculosis_global": "Tuberculosis AND (Treatment OR WHO Guidelines)",
    "cholera_bangladesh": "Cholera AND Bangladesh",
    "cholera_global": "Cholera AND (Management OR Treatment)",
    "leptospirosis_bangladesh": "Leptospirosis AND Bangladesh",
    "leptospirosis_global": "Leptospirosis AND Treatment",
    "leishmaniasis_bangladesh": "Leishmaniasis AND Bangladesh",
    "leishmaniasis_global": "Leishmaniasis AND Treatment",
    "influenza_bangladesh": "Influenza AND Bangladesh",
    "influenza_global": "Influenza AND Treatment",
    # Non-Communicable Diseases (NCDs)
    "diabetes_bangladesh": "Diabetes AND Bangladesh",
    "diabetes_global": "Diabetes AND (Management OR Treatment)",
    "hypertension_bangladesh": "Hypertension AND Bangladesh",
    "hypertension_global": "Hypertension AND Guidelines",
    "cardiovascular_bangladesh": "Cardiovascular Diseases AND Bangladesh",
    "cardiovascular_global": "Cardiovascular Diseases AND Treatment",
    "ckd_bangladesh": "Chronic Kidney Disease AND Bangladesh",
    "ckd_global": "Chronic Kidney Disease AND Management",
    "cancer_bangladesh": "Cancer AND Bangladesh",
    "cancer_global": "Cancer AND (Treatment OR Management)",
    # Maternal & Child Health
    "maternal_health_bangladesh": "Maternal Health AND Bangladesh",
    "maternal_health_global": "Maternal Health AND Guidelines",
    "neonatal_care_bangladesh": "Neonatal Care AND Bangladesh",
    "neonatal_care_global": "Neonatal Care AND WHO Guidelines",
    "malnutrition_bangladesh": "Malnutrition AND Bangladesh",
    "malnutrition_global": "Malnutrition AND Treatment",
    "immunization_bangladesh": "Vaccination AND Bangladesh",
    "immunization_global": "Immunization AND WHO Guidelines",
    # Public Health & Surveillance
    "surveillance_bangladesh": "Disease Surveillance AND Bangladesh",
    "surveillance_global": "Disease Surveillance AND WHO",
    "outbreak_management_bangladesh": "Outbreak Response AND Bangladesh",
    "outbreak_management_global": "Outbreak Response AND Guidelines",
    "health_policy_bangladesh": "Health Policy AND Bangladesh",
    "health_policy_global": "Health Policy AND Guidelines",
    # Drug & Treatment Protocols
    "amr_bangladesh": "Antibiotic Resistance AND Bangladesh",
    "amr_global": "Antimicrobial Resistance AND WHO Guidelines",
    "essential_medicines_bangladesh": "Essential Medicines AND Bangladesh",
    "essential_medicines_global": "Essential Medicines AND WHO Guidelines",
    "drug_pricing_bangladesh": "Drug Pricing AND Bangladesh",
    "drug_pricing_global": "Drug Pricing AND Policies",
    # General Bangladesh Healthcare Queries
    "healthcare_system_bangladesh": "Healthcare System AND Bangladesh",
    "primary_healthcare_bangladesh": "Primary Healthcare AND Bangladesh",
    "rural_health_services_bangladesh": "Rural Health Services AND Bangladesh",
    "community_health_workers_bangladesh": "Community Health Workers AND Bangladesh",
    # General Thematic Searches
    "thematic_infectious_diseases_bd": "Infectious Diseases AND Bangladesh",
    "thematic_ncd_bd": "Non-communicable Diseases AND Bangladesh",
    "thematic_public_health_guidelines_bd": "Public Health Guidelines AND Bangladesh",
    "thematic_disease_surveillance_reports_bd": "Bangladesh Disease Surveillance Reports",
}


def fetch_pubmed_id(query: str, max_results: int = 100) -> list:
    """
    Fetch PubMed IDs for a given search query.

    Args:
        query (str): Search query for PubMed
        max_results (int): Maximum number of results to return

    Returns:
        list: List of PubMed IDs
    """
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]


def fetch_pubmed_abstracts(id_list: list, batch_size: int = 20) -> list:
    """
    Fetch abstracts for a list of PubMed IDs.

    Args:
        id_list (list): List of PubMed IDs
        batch_size (int): Number of IDs to process in each batch

    Returns:
        list: List of dictionaries containing article information
    """
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

        time.sleep(0.3)  # NCBI rate limits

    return abstracts


def save_to_json(data: list, output_file: str) -> None:
    """
    Save data to a JSON file.

    Args:
        data (list): Data to save
        output_file (str): Path to output file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def fetch_and_save_pubmed_abstracts(max_results: int = 100) -> None:
    """
    Fetch and save PubMed abstracts for all search queries.

    Args:
        max_results (int): Maximum number of results per query
    """
    for tag, query in SEARCH_QUERIES.items():
        ids = fetch_pubmed_id(query, max_results=100)
        print(f"Found {len(ids)} articles for query '{tag}'.")

        abstracts = fetch_pubmed_abstracts(ids)
        # Auto-tagging source type
        source_type = "Bangladesh-specific" if "Bangladesh" in query else "Global"
        for doc in abstracts:
            doc["source_type"] = source_type

        output_file = f"data/processed/{tag}.json"
        save_to_json(abstracts, output_file)
        print(f"Saved {len(abstracts)} articles to {output_file}")


if __name__ == "__main__":
    fetch_and_save_pubmed_abstracts(max_results=100)
