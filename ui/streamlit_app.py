import streamlit as st
import requests

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
    .medication-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .schedule-visual {
        background: #e3f2fd;
        padding: 0.5rem;
        border-radius: 6px;
        margin-top: 0.5rem;
        font-weight: bold;
        text-align: center;
    }
    .drug-found {
        background: #d4edda;
        color: #155724;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .drug-not-found {
        background: #fff3cd;
        color: #856404;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
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
    .medication-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
                except Exception as e:
                    st.write(f"Could not retrieve system stats{e}")

        return age, gender, api_healthy


def render_enhanced_medication_input():
    """Render enhanced medication input with dropdown schedules."""
    st.header("💊 Medications")

    # Initialize session state
    if "medications" not in st.session_state:
        st.session_state.medications = [
            {"name": "", "morning": 0, "noon": 0, "night": 0}
        ]

    medications_data = []

    for i, med_data in enumerate(st.session_state.medications):
        with st.container():
            st.markdown('<div class="medication-card">', unsafe_allow_html=True)

            # Medication name input
            col1, col2 = st.columns([2, 1])

            with col1:
                med_name = st.text_input(
                    f"Medication {i + 1}",
                    value=med_data["name"],
                    key=f"med_name_{i}",
                    placeholder="Type medication name...",
                )

                # Update session state
                st.session_state.medications[i]["name"] = med_name

                # Show suggestions
                if med_name and len(med_name) > 2:
                    suggestions = search_drugs(med_name)
                    if suggestions:
                        selected = st.selectbox(
                            "Suggestions:",
                            [""] + suggestions,
                            key=f"suggestions_{i}",
                        )
                        if selected:
                            st.session_state.medications[i]["name"] = selected
                            st.rerun()

            with col2:
                if i > 0:
                    if st.button("🗑️", key=f"remove_{i}", help="Remove medication"):
                        st.session_state.medications.pop(i)
                        st.rerun()

            # Enhanced schedule input with dropdowns
            st.markdown("**Dosing Schedule:**")
            col_morning, col_noon, col_night = st.columns(3)

            with col_morning:
                morning_dose = st.selectbox(
                    "🌅 Morning",
                    [0, 0.5, 1, 1.5, 2, "Custom"],
                    index=[0, 0.5, 1, 1.5, 2, "Custom"].index(
                        med_data.get("morning", 0)
                    )
                    if med_data.get("morning", 0) in [0, 0.5, 1, 1.5, 2]
                    else 5,
                    key=f"morning_{i}",
                )
                if morning_dose == "Custom":
                    morning_dose = st.number_input(
                        "Custom morning dose",
                        min_value=0.0,
                        step=0.25,
                        key=f"morning_custom_{i}",
                        value=med_data.get("morning", 0)
                        if med_data.get("morning", 0) not in [0, 0.5, 1, 1.5, 2]
                        else 0.0,
                    )
                st.session_state.medications[i]["morning"] = morning_dose

            with col_noon:
                noon_dose = st.selectbox(
                    "☀️ Noon",
                    [0, 0.5, 1, 1.5, 2, "Custom"],
                    index=[0, 0.5, 1, 1.5, 2, "Custom"].index(med_data.get("noon", 0))
                    if med_data.get("noon", 0) in [0, 0.5, 1, 1.5, 2]
                    else 5,
                    key=f"noon_{i}",
                )
                if noon_dose == "Custom":
                    noon_dose = st.number_input(
                        "Custom noon dose",
                        min_value=0.0,
                        step=0.25,
                        key=f"noon_custom_{i}",
                        value=med_data.get("noon", 0)
                        if med_data.get("noon", 0) not in [0, 0.5, 1, 1.5, 2]
                        else 0.0,
                    )
                st.session_state.medications[i]["noon"] = noon_dose

            with col_night:
                night_dose = st.selectbox(
                    "🌙 Night",
                    [0, 0.5, 1, 1.5, 2, "Custom"],
                    index=[0, 0.5, 1, 1.5, 2, "Custom"].index(med_data.get("night", 0))
                    if med_data.get("night", 0) in [0, 0.5, 1, 1.5, 2]
                    else 5,
                    key=f"night_{i}",
                )
                if night_dose == "Custom":
                    night_dose = st.number_input(
                        "Custom night dose",
                        min_value=0.0,
                        step=0.25,
                        key=f"night_custom_{i}",
                        value=med_data.get("night", 0)
                        if med_data.get("night", 0) not in [0, 0.5, 1, 1.5, 2]
                        else 0.0,
                    )
                st.session_state.medications[i]["night"] = night_dose

            # Visual schedule representation
            if any([morning_dose, noon_dose, night_dose]):
                # Convert "Custom" back to numeric for display
                morning_display = (
                    morning_dose
                    if morning_dose != "Custom"
                    else med_data.get("morning", 0)
                )
                noon_display = (
                    noon_dose if noon_dose != "Custom" else med_data.get("noon", 0)
                )
                night_display = (
                    night_dose if night_dose != "Custom" else med_data.get("night", 0)
                )

                schedule_visual = (
                    f"🌅 {morning_display} | ☀️ {noon_display} | 🌙 {night_display}"
                )
                st.markdown(f"**Schedule:** {schedule_visual}")

            # Drug information display
            if med_name:
                drug_info = get_drug_info(med_name)
                if drug_info and drug_info.get("found"):
                    st.success("✅ Found in database")
                elif med_name.strip():
                    st.warning("⚠️ Not found in database - will search literature")

            st.markdown("</div>", unsafe_allow_html=True)

            # Store medication data
            if med_name.strip() and any([morning_dose, noon_dose, night_dose]):
                # Convert doses to float for schedule string
                morning_val = (
                    float(morning_dose)
                    if morning_dose != "Custom"
                    else float(med_data.get("morning", 0))
                )
                noon_val = (
                    float(noon_dose)
                    if noon_dose != "Custom"
                    else float(med_data.get("noon", 0))
                )
                night_val = (
                    float(night_dose)
                    if night_dose != "Custom"
                    else float(med_data.get("night", 0))
                )

                schedule_str = f"{morning_val}+{noon_val}+{night_val}"
                medications_data.append(
                    {
                        "name": med_name.strip(),
                        "schedule": schedule_str,
                        "morning": morning_val,
                        "noon": noon_val,
                        "night": night_val,
                    }
                )

    # Add medication button
    if st.button("➕ Add Another Medication"):
        st.session_state.medications.append(
            {"name": "", "morning": 0, "noon": 0, "night": 0}
        )
        st.rerun()

    # Enhanced schedule format help
    with st.expander("ℹ️ Enhanced Schedule Format Help"):
        st.markdown("""
        **Enhanced Dosing Schedule with Visual Interface**
        
        **Dropdown Options:**
        - **0**: No dose at this time
        - **0.5**: Half tablet/dose
        - **1**: One tablet/dose  
        - **1.5**: One and half tablets/dose
        - **2**: Two tablets/dose
        - **Custom**: Enter any custom dose amount
        
        **Visual Schedule Display:**
        🌅 Morning | ☀️ Noon | 🌙 Night
        
        **Examples:**
        - `🌅 1 | ☀️ 0 | 🌙 1` = Morning and night dosing
        - `🌅 0.5 | ☀️ 0.5 | 🌙 0.5` = Half dose three times daily
        - `🌅 2 | ☀️ 1 | 🌙 1` = Higher morning dose
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


def render_enhanced_medication_input():
    """Render enhanced medication input with dropdown schedules."""
    st.header("💊 Enhanced Medication Input")

    # Initialize session state for enhanced input
    if "enhanced_medications" not in st.session_state:
        st.session_state.enhanced_medications = [
            {"name": "", "morning": 0, "noon": 0, "night": 0}
        ]

    medications_data = []

    for i, med_data in enumerate(st.session_state.enhanced_medications):
        with st.container():
            st.markdown('<div class="medication-card">', unsafe_allow_html=True)

            # Medication name input
            col1, col2 = st.columns([3, 1])

            with col1:
                med_name = st.text_input(
                    f"Medication {i + 1}",
                    value=med_data.get("name", ""),
                    key=f"enhanced_med_name_{i}",
                    placeholder="Type medication name...",
                )

                # Update session state
                st.session_state.enhanced_medications[i]["name"] = med_name

                # Show suggestions
                if med_name and len(med_name) > 2:
                    suggestions = search_drugs(med_name)
                    if suggestions:
                        selected = st.selectbox(
                            "Suggestions:",
                            [""] + suggestions,
                            key=f"enhanced_suggestions_{i}",
                        )
                        if selected and selected != med_name:
                            st.session_state.enhanced_medications[i]["name"] = selected
                            st.rerun()

            with col2:
                if i > 0:
                    if st.button(
                        "🗑️", key=f"enhanced_remove_{i}", help="Remove medication"
                    ):
                        st.session_state.enhanced_medications.pop(i)
                        st.rerun()

            # Enhanced schedule input with dropdowns
            st.markdown("**Dosing Schedule:**")
            col_morning, col_noon, col_night = st.columns(3)

            dose_options = [0, 0.5, 1, 1.5, 2, "Custom"]

            with col_morning:
                current_morning = med_data.get("morning", 0)
                if current_morning in dose_options:
                    morning_idx = dose_options.index(current_morning)
                else:
                    morning_idx = len(dose_options) - 1  # Custom

                morning_dose = st.selectbox(
                    "🌅 Morning",
                    dose_options,
                    index=morning_idx,
                    key=f"enhanced_morning_{i}",
                )
                if morning_dose == "Custom":
                    morning_dose = st.number_input(
                        "Custom morning dose",
                        min_value=0.0,
                        step=0.25,
                        value=float(current_morning)
                        if current_morning not in dose_options[:-1]
                        else 0.0,
                        key=f"enhanced_morning_custom_{i}",
                    )
                st.session_state.enhanced_medications[i]["morning"] = morning_dose

            with col_noon:
                current_noon = med_data.get("noon", 0)
                if current_noon in dose_options:
                    noon_idx = dose_options.index(current_noon)
                else:
                    noon_idx = len(dose_options) - 1  # Custom

                noon_dose = st.selectbox(
                    "☀️ Noon", dose_options, index=noon_idx, key=f"enhanced_noon_{i}"
                )
                if noon_dose == "Custom":
                    noon_dose = st.number_input(
                        "Custom noon dose",
                        min_value=0.0,
                        step=0.25,
                        value=float(current_noon)
                        if current_noon not in dose_options[:-1]
                        else 0.0,
                        key=f"enhanced_noon_custom_{i}",
                    )
                st.session_state.enhanced_medications[i]["noon"] = noon_dose

            with col_night:
                current_night = med_data.get("night", 0)
                if current_night in dose_options:
                    night_idx = dose_options.index(current_night)
                else:
                    night_idx = len(dose_options) - 1  # Custom

                night_dose = st.selectbox(
                    "🌙 Night", dose_options, index=night_idx, key=f"enhanced_night_{i}"
                )
                if night_dose == "Custom":
                    night_dose = st.number_input(
                        "Custom night dose",
                        min_value=0.0,
                        step=0.25,
                        value=float(current_night)
                        if current_night not in dose_options[:-1]
                        else 0.0,
                        key=f"enhanced_night_custom_{i}",
                    )
                st.session_state.enhanced_medications[i]["night"] = night_dose

            # Visual schedule representation
            if any([morning_dose, noon_dose, night_dose]):
                schedule_visual = f"🌅 {morning_dose} | ☀️ {noon_dose} | 🌙 {night_dose}"
                st.markdown(
                    f'<div class="schedule-visual">{schedule_visual}</div>',
                    unsafe_allow_html=True,
                )

            # Drug information display
            if med_name:
                drug_info = get_drug_info(med_name)
                if drug_info and drug_info.get("found"):
                    st.markdown(
                        '<span class="drug-found">✅ Found in database</span>',
                        unsafe_allow_html=True,
                    )
                elif med_name.strip():
                    st.markdown(
                        '<span class="drug-not-found">⚠️ Not found in database - will search literature</span>',
                        unsafe_allow_html=True,
                    )

            st.markdown("</div>", unsafe_allow_html=True)

            # Store medication data
            if med_name.strip() and any([morning_dose, noon_dose, night_dose]):
                schedule_str = f"{morning_dose}+{noon_dose}+{night_dose}"
                medications_data.append(
                    {
                        "name": med_name.strip(),
                        "schedule": schedule_str,
                        "morning": morning_dose,
                        "noon": noon_dose,
                        "night": night_dose,
                    }
                )

    # Add medication button
    if st.button("➕ Add Another Medication", key="enhanced_add_med"):
        st.session_state.enhanced_medications.append(
            {"name": "", "morning": 0, "noon": 0, "night": 0}
        )
        st.rerun()

    # Schedule format help
    with st.expander("ℹ️ Enhanced Schedule Help"):
        st.markdown("""
        **Enhanced Dosing Schedule:**
        
        - Use dropdown menus to select common doses (0, 0.5, 1, 1.5, 2 tablets/pills)
        - Select "Custom" for other dose amounts
        - Visual representation shows your schedule at a glance
        - 🌅 Morning, ☀️ Noon, 🌙 Night dosing times
        
        **Examples:**
        - Morning: 1, Noon: 0, Night: 1 = Twice daily dosing
        - Morning: 0.5, Noon: 0, Night: 0.5 = Half tablet twice daily
        - All times: 1 = Three times daily
        """)

    return medications_data


def main():
    """Main application function."""
    # Render header
    render_header()

    # Render sidebar and get patient info
    age, gender, api_healthy = render_sidebar()

    # Main content area
    col1, col2 = st.columns([1.2, 0.8])

    with col1:
        # Enhanced medication input section
        medications_data = render_enhanced_medication_input()

    with col2:
        # Advice generation section
        render_advice_section(medications_data, age, gender, api_healthy)

    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
