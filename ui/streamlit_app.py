"""Streamlit frontend for the Medical Guideline RAG system."""

import streamlit as st
import requests
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add config to Python path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import API_PORT, UI_PORT

# Configure page
st.set_page_config(
    page_title="Medical Advisor",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API Configuration
API_BASE = f"http://localhost:{API_PORT}"

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .section-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        border: 1px solid #e0e0e0;
    }
    .medication-section {
        background: #ffe4e1;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid #ffb3ba;
    }
    .patient-info-section {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #87ceeb;
    }
    .advice-container {
        background: #f9f9f9;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid #ddd;
    }
    .dos-section {
        background: #d4ffda;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem;
        border-left: 4px solid #4CAF50;
    }
    .donts-section {
        background: #ffe4e1;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem;
        border-left: 4px solid #f44336;
    }
    .results-section {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid #ccc;
        min-height: 200px;
    }
    .disclaimer-section {
        background: #fff9c4;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        border: 1px solid #ffeaa7;
    }
    .api-status {
        background: #e8f5e8;
        padding: 0.5rem;
        border-radius: 6px;
        border: 1px solid #4CAF50;
        margin-bottom: 1rem;
    }
    .medication-input {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .schedule-help {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


def check_api_health() -> bool:
    """Check if the API is running and healthy."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def search_drugs(query: str) -> List[str]:
    """Search for drug names via API."""
    if len(query) < 2:
        return []

    try:
        response = requests.get(
            f"{API_BASE}/search_drugs", params={"query": query, "limit": 10}, timeout=10
        )
        if response.status_code == 200:
            return response.json()["results"]
    except Exception as e:
        st.error(f"Error searching drugs: {e}")
    return []


def get_drug_info(drug_name: str) -> Optional[Dict]:
    """Get information about a specific drug."""
    try:
        response = requests.get(f"{API_BASE}/drug_info/{drug_name}", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def render_header():
    """Render the main header."""
    st.markdown(
        """
    <div class="main-header">
        <h1>🩺 AI-Powered Medical Advisor</h1>
        <p>Get evidence-based medication guidance powered by medical literature and drug databases</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Render the sidebar with patient information."""
    with st.sidebar:
        st.header("👤 Patient Information")

        # Check API status
        api_healthy = check_api_health()
        if api_healthy:
            st.success("🟢 API Connected")
        else:
            st.error("🔴 API Disconnected")
            st.warning("Please ensure the API server is running on port 8000")

        st.markdown("---")

        # Patient details
        age = st.number_input(
            "Age", min_value=1, max_value=120, value=30, help="Patient's age in years"
        )

        gender = st.selectbox(
            "Gender",
            ["M", "F", "O"],
            format_func=lambda x: {"M": "Male", "F": "Female", "O": "Other"}[x],
            help="Patient's gender",
        )

        st.markdown("---")

        # System information
        with st.expander("ℹ️ System Information"):
            st.write(f"**API Endpoint:** {API_BASE}")
            st.write(
                f"**Current Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            if api_healthy:
                try:
                    stats_response = requests.get(f"{API_BASE}/stats", timeout=5)
                    if stats_response.status_code == 200:
                        stats = stats_response.json()
                        st.json(stats)
                except:
                    st.write("Could not retrieve system stats")

        return age, gender, api_healthy


def render_medication_input():
    """Render medication input section."""
    st.header("💊 Medications")

    # Initialize session state
    if "medications" not in st.session_state:
        st.session_state.medications = [""]
    if "schedules" not in st.session_state:
        st.session_state.schedules = [""]

    # Dynamic medication inputs
    medications_data = []

    for i in range(len(st.session_state.medications)):
        with st.container():
            st.markdown(f'<div class="medication-card">', unsafe_allow_html=True)

            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                # Medication name input with search
                med_key = f"med_{i}"
                current_med = st.text_input(
                    f"Medication {i + 1}",
                    value=st.session_state.medications[i],
                    key=med_key,
                    placeholder="Type medication name...",
                    help="Start typing to search for medications",
                )

                # Update session state
                st.session_state.medications[i] = current_med

                # Show suggestions if typing
                if current_med and len(current_med) > 2:
                    suggestions = search_drugs(current_med)
                    if suggestions:
                        selected = st.selectbox(
                            f"Suggestions for Medication {i + 1}:",
                            [""] + suggestions,
                            key=f"suggestions_{i}",
                        )
                        if selected:
                            st.session_state.medications[i] = selected
                            st.rerun()

            with col2:
                schedule = st.text_input(
                    "Schedule",
                    value=st.session_state.schedules[i],
                    key=f"schedule_{i}",
                    placeholder="1+0+1",
                    help="Format: Morning+Noon+Night",
                )
                st.session_state.schedules[i] = schedule

            with col3:
                if i > 0:  # Don't show remove button for first medication
                    if st.button(
                        "❌", key=f"remove_{i}", help="Remove this medication"
                    ):
                        st.session_state.medications.pop(i)
                        st.session_state.schedules.pop(i)
                        st.rerun()

            # Show drug info if available
            if current_med:
                drug_info = get_drug_info(current_med)
                if drug_info and drug_info.get("found"):
                    st.success(f"✅ Found in database")
                elif current_med.strip():
                    st.warning(f"⚠️ Not found in database - will search literature")

            st.markdown("</div>", unsafe_allow_html=True)

            # Store valid medication data
            if current_med.strip() and schedule.strip():
                medications_data.append(
                    {"name": current_med.strip(), "schedule": schedule.strip()}
                )

    # Add/Remove medication buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("➕ Add Medication"):
            st.session_state.medications.append("")
            st.session_state.schedules.append("")
            st.rerun()

    with col2:
        if st.button("🗑️ Clear All"):
            st.session_state.medications = [""]
            st.session_state.schedules = [""]
            st.rerun()

    # Schedule format help
    with st.expander("ℹ️ Schedule Format Help"):
        st.markdown("""
        **Schedule Format: Morning+Noon+Night**
        
        Examples:
        - `1+0+1` = 1 tablet morning, 0 noon, 1 night
        - `0+1+0` = 1 tablet at noon only
        - `1+1+1` = 1 tablet three times daily
        - `2+0+2` = 2 tablets morning and night
        - `0.5+0+0.5` = Half tablet morning and night
        """)

    return medications_data


def render_advice_section(medications_data, age, gender, api_healthy):
    """Render the advice generation section."""
    st.header("🔍 Get Medication Advice")

    # Validation and advice generation
    if not medications_data:
        st.warning("Please add at least one medication with a schedule to get advice.")
        return

    if not api_healthy:
        st.error("Cannot generate advice - API service is not available.")
        return

    # Show medication summary
    with st.expander("📋 Medication Summary", expanded=True):
        for i, med in enumerate(medications_data, 1):
            st.write(f"**{i}.** {med['name']} - Schedule: {med['schedule']}")

    # Generate advice button
    if st.button(
        "🚀 Generate Medication Advice",
        type="primary",
        help="Generate evidence-based medication advice",
    ):
        # Prepare request data
        request_data = {
            "meds": [med["name"] for med in medications_data],
            "schedule": [med["schedule"] for med in medications_data],
            "age": age,
            "gender": gender,
        }

        # Show loading animation
        with st.spinner("🔄 Analyzing medications and generating advice..."):
            try:
                # Call API
                response = requests.post(
                    f"{API_BASE}/advise",
                    json=request_data,
                    timeout=120,  # Increased timeout for LLM processing
                )

                if response.status_code == 200:
                    result = response.json()
                    render_advice_results(result)
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"❌ Error: {response.status_code} - {error_detail}")

            except requests.exceptions.Timeout:
                st.error(
                    "⏱️ Request timed out. The server might be busy. Please try again."
                )
            except requests.exceptions.ConnectionError:
                st.error(
                    "🔌 Connection error. Please check if the API server is running."
                )
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")


def render_advice_results(result):
    """Render the generated advice results."""
    st.success("✅ Advice generated successfully!")

    # Show metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Medications Processed", result.get("medications_processed", 0))
    with col2:
        st.metric("Database Matches", result.get("medications_found", 0))
    with col3:
        st.metric("Research Articles", result.get("pubmed_articles", 0))

    # Display the main advice
    st.markdown("---")

    # Format and display advice
    advice_text = result.get("advice", "")
    if advice_text:
        st.markdown('<div class="advice-section">', unsafe_allow_html=True)
        st.markdown(advice_text)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error("No advice was generated. Please try again.")

    # Show sources if available
    sources = result.get("context_sources", [])
    if sources:
        with st.expander("📚 Research Sources Used"):
            for i, source in enumerate(sources, 1):
                if source.strip():
                    st.write(f"{i}. {source}")

    # Download option
    if advice_text:
        st.download_button(
            label="📄 Download Advice as Text",
            data=advice_text,
            file_name=f"medication_advice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
        )


def render_footer():
    """Render the footer with disclaimers."""
    st.markdown("---")
    st.markdown(
        """
    <div class="warning-box">
        <h4>⚠️ Important Medical Disclaimer</h4>
        <p>
        This tool provides <strong>educational information only</strong> and is not a substitute for professional medical advice, 
        diagnosis, or treatment. Always consult with a qualified healthcare provider for medical decisions and before making 
        any changes to your medication regimen.
        </p>
        <p>
        <strong>For immediate medical concerns or emergencies, contact your healthcare provider or emergency services immediately.</strong>
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Additional information
    with st.expander("ℹ️ About This Tool"):
        st.markdown("""
        **Medical Advisor System Features:**
        - 🔍 **Evidence-Based**: Uses medical literature and drug databases
        - 🤖 **AI-Powered**: Advanced language models for comprehensive advice
        - 📊 **Data Sources**: PubMed research articles and MedEx drug database
        - 🛡️ **Safety-Focused**: Emphasizes warnings and contraindications
        
        **Technology Stack:**
        - FastAPI backend with vector search
        - Google Gemini for advice generation
        - Sentence transformers for semantic search
        - Streamlit for user interface
        """)


def main():
    """Main application function."""
    # Render header
    render_header()

    # Render sidebar and get patient info
    age, gender, api_healthy = render_sidebar()

    # Main content area
    col1, col2 = st.columns([1.2, 0.8])

    with col1:
        # Medication input section
        medications_data = render_medication_input()

    with col2:
        # Advice generation section
        render_advice_section(medications_data, age, gender, api_healthy)

    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
