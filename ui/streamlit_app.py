import streamlit as st
import requests
import re
import markdown
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from typing import Dict
from dataclasses import dataclass
from datetime import datetime
import io

# Configure page
st.set_page_config(
    page_title="Medical Advisor",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Simple and robust CSS styling
st.markdown("""
<style>
/* === GLOBAL THEME === */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    color: white !important;
}

/* === HIDE STREAMLIT ELEMENTS === */
#MainMenu, footer, header, .stDeployButton { display: none !important; }

/* === LAYOUT === */
.main .block-container {
    max-width: 1200px !important;
    padding: 1rem !important;
}

/* === CUSTOM COMPONENTS === */
.medical-header {
    background: rgba(30, 41, 59, 0.9);
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

.custom-card {
    background: rgba(30, 41, 59, 0.9) !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    border-radius: 12px !important;
    padding: 2rem !important;
    margin: 1rem 0 !important;
}

/* === STEP INDICATOR === */
.step-indicator {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin: 2rem 0;
}

.step-number {
    width: 3rem;
    height: 3rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: white;
}

.step-completed { background: #10b981; }
.step-current { background: #3b82f6; }
.step-pending { background: #374151; border: 2px solid #6b7280; }

.step-connector {
    width: 3rem;
    height: 3px;
    background: #6b7280;
    margin-top: 1.5rem;
}
.step-connector.completed { background: #10b981; }

/* === INPUTS === */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: rgba(30, 41, 59, 0.9) !important;
    color: white !important;
    border: 2px solid rgba(59, 130, 246, 0.3) !important;
    border-radius: 8px !important;
}

.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
}

/* === BUTTONS === */
.stButton button {
    background: #3b82f6 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}

.stButton button:hover {
    background: #2563eb !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
}

/* === MEDICATION COMPONENTS === */
.medication-item {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.dosage-item {
    background: rgba(59, 130, 246, 0.1);
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    margin-bottom: 1rem;
}

/* === DOSE CONTROLS === */
.dosage-controls button {
    height: 3.5rem !important;
    font-size: 2rem !important;
    font-weight: 900 !important;
    border-radius: 8px !important;
    border: 3px solid !important;
}

/* Decrease button - Red */
.dosage-controls > div:first-child button {
    background: #dc2626 !important;
    border-color: #b91c1c !important;
    color: white !important;
}

/* Increase button - Green */
.dosage-controls > div:last-child button {
    background: #059669 !important;
    border-color: #047857 !important;
    color: white !important;
}

.dose-value {
    background: rgba(30, 41, 59, 0.9) !important;
    border: 3px solid #3b82f6 !important;
    border-radius: 8px !important;
    color: white !important;
    font-size: 1.5rem !important;
    font-weight: bold !important;
    height: 3.5rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-family: monospace !important;
}

/* === CHAT INTERFACE === */
.chat-container {
    max-height: 70vh;
    overflow-y: auto;
    padding: 1rem;
}

.user-message {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.5);
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0 1rem 20%;
}

.assistant-message {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid rgba(16, 185, 129, 0.5);
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 20% 1rem 0;
}

/* === IMPROVED TEXT FORMATTING === */
.formatted-content {
    line-height: 1.6 !important;
    font-size: 0.95rem !important;
}

.formatted-content h1, .formatted-content h2 {
    color: #3b82f6 !important;
    margin: 1.5rem 0 1rem 0 !important;
    font-weight: 600 !important;
    border-bottom: 2px solid rgba(59, 130, 246, 0.3) !important;
    padding-bottom: 0.5rem !important;
}

.formatted-content h1 {
    font-size: 1.4rem !important;
}

.formatted-content h2 {
    font-size: 1.2rem !important;
}

.formatted-content h3, .formatted-content h4 {
    color: #10b981 !important;
    margin: 1.2rem 0 0.8rem 0 !important;
    font-weight: 500 !important;
    font-size: 1.1rem !important;
}

.formatted-content p {
    margin: 0.8rem 0 !important;
    text-align: justify !important;
}

.formatted-content ul, .formatted-content ol {
    margin: 0.8rem 0 !important;
    padding-left: 1.5rem !important;
}

.formatted-content li {
    margin: 0.4rem 0 !important;
    line-height: 1.5 !important;
}

.formatted-content strong {
    color: #fbbf24 !important;
    font-weight: 600 !important;
}

.formatted-content em {
    color: #a78bfa !important;
    font-style: italic !important;
}

.formatted-content table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 1rem 0 !important;
    background: rgba(30, 41, 59, 0.5) !important;
}

.formatted-content th, .formatted-content td {
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    padding: 0.5rem !important;
    text-align: left !important;
}

.formatted-content th {
    background: rgba(59, 130, 246, 0.2) !important;
    font-weight: 600 !important;
}

/* === STREAMLIT MARKDOWN TABLES === */
.stMarkdown table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 1rem 0 !important;
    background: rgba(30, 41, 59, 0.5) !important;
    color: white !important;
}

.stMarkdown th, .stMarkdown td {
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    padding: 0.75rem !important;
    text-align: left !important;
    color: white !important;
}

.stMarkdown th {
    background: rgba(59, 130, 246, 0.2) !important;
    font-weight: 600 !important;
}

.stMarkdown tbody tr:nth-child(even) {
    background: rgba(30, 41, 59, 0.3) !important;
}

.stMarkdown tbody tr:hover {
    background: rgba(59, 130, 246, 0.1) !important;
}

/* === SECTION SPACING === */
.content-section {
    margin: 1rem 0 !important;
    padding: 0 !important;
}

.section-spacing {
    margin-bottom: 0.5rem !important;
}

.message-metadata {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.5rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 0.8rem;
    text-align: center;
}

/* === SIDEBAR === */
.sidebar-section {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}

/* === DISCLAIMER === */
.compact-disclaimer {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 8px;
    padding: 1rem;
    margin: 2rem 0;
    text-align: center;
    color: #fca5a5;
    font-size: 0.9rem;
}

/* === ANIMATIONS === */
.loading-dots {
    display: flex;
    gap: 0.25rem;
    align-items: center;
}

.loading-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #3b82f6;
    animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) { animation-delay: -0.32s; }
.loading-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
    0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
    40% { transform: scale(1); opacity: 1; }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* === OVERRIDES === */
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.95) !important;
}

/* Force dark theme on any remaining white elements */
div[style*="background-color: white"], 
div[style*="background: white"] {
    background: rgba(30, 41, 59, 0.8) !important;
}
</style>
""", unsafe_allow_html=True)

@dataclass
class PatientInfo:
    age: int
    gender: str  

@dataclass
class Medication:
    id: str
    name: str
    morning: float
    noon: float
    night: float

class MedicalAdvisorApp:
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.dose_options = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize all session state variables"""
        defaults = {
            'current_step': 1,
            'patient_info': None,
            'medications': [],
            'show_chat': False,
            'chat_messages': [],
            'advice_result': None,
            'is_loading': False,
            'suggestions': {},
            'loading_suggestions': {},
            'errors': {}
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def clean_and_format_content(self, content: str) -> str:
        """Clean and format content for better display"""
        if not content:
            return ""
        
        # Remove excessive whitespace and normalize line breaks
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        content = content.strip()
        
        # Fix common markdown formatting issues
        content = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', content)
        content = re.sub(r'\*([^*]+)\*', r'*\1*', content)
        
        # Ensure proper spacing around headers
        content = re.sub(r'(#+)\s*([^\n]+)', r'\1 \2', content)
        content = re.sub(r'([^\n])\n(#+\s)', r'\1\n\n\2', content)
        content = re.sub(r'(#+[^\n]+)\n([^\n#])', r'\1\n\n\2', content)
        
        # Fix list formatting
        content = re.sub(r'\n(-|\*|\d+\.)\s*([^\n]+)', r'\n\1 \2', content)
        
        # Remove excessive spaces in tables
        content = re.sub(r'\|\s+', '| ', content)
        content = re.sub(r'\s+\|', ' |', content)
        
        return content
    
    def format_content_for_display(self, content: str) -> str:
        """Format content for HTML display"""
        cleaned_content = self.clean_and_format_content(content)
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            cleaned_content,
            extensions=['tables', 'nl2br', 'fenced_code']
        )
        
        # Clean up HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Add CSS classes for better styling
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'table']):
            existing_class = tag.get('class', [])
            existing_class.append('formatted-content')
            tag['class'] = existing_class
        
        return str(soup)

    def check_api_status(self):
        """Check if the API is available"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def render_header(self):
        """Render header with API status indicator"""
        api_status = self.check_api_status()
        status_color = "#10b981" if api_status else "#ef4444"
        status_text = "API Online" if api_status else "API Offline"
        
        st.markdown(f"""
        <div class="medical-header">
            <div style="display: flex; align-items: center; justify-content: space-between; max-width: 1200px; margin: 0 auto; padding: 0 1rem;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <div style="width: 2rem; height: 2rem; background: #3b82f6; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                            <span style="color: white; font-weight: bold; font-size: 1.2rem;">🩺</span>
                        </div>
                        <h1 style="font-size: 2rem; font-weight: bold; background: linear-gradient(45deg, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
                            Medical Advisor
                        </h1>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div style="width: 8px; height: 8px; background: {status_color}; border-radius: 50%; animation: pulse 2s infinite;"></div>
                    <span style="font-size: 0.8rem; color: {status_color};">{status_text}</span>
                </div>
            </div>
            <p style="color: rgba(255, 255, 255, 0.8); margin-top: 0.5rem; text-align: center;">
                AI-powered medication guidance using evidence-based medical literature
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # New Consultation button when in chat
        if st.session_state.show_chat:
            col1, col2, col3 = st.columns([1, 4, 1])
            with col3:
                if st.button("New Consultation", key="header_reset"):
                    self.reset_flow()
    
    def render_step_indicator(self):
        """Render step indicator showing current progress"""
        steps = [
            {"number": 1, "title": "Patient Information", "completed": st.session_state.current_step > 1},
            {"number": 2, "title": "Medication Details", "completed": st.session_state.current_step > 2 or st.session_state.show_chat},
            {"number": 3, "title": "AI Consultation", "completed": st.session_state.show_chat}
        ]
        
        st.markdown('<div class="step-indicator">', unsafe_allow_html=True)
        
        # Create columns for steps and connectors
        cols = st.columns([1, 0.5, 1, 0.5, 1])
        
        for i, step in enumerate(steps):
            col_idx = i * 2
            
            # Determine step class
            if step["completed"]:
                step_class = "step-completed"
            elif step["number"] == st.session_state.current_step:
                step_class = "step-current"
            else:
                step_class = "step-pending"
            
            with cols[col_idx]:
                st.markdown(f"""
                <div class="step-item">
                    <div class="step-number {step_class}">{step["number"]}</div>
                    <div style="margin-left: 0.5rem;">
                        <div style="font-weight: 500; font-size: 0.9rem;">{step["title"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Add connector between steps
            if i < len(steps) - 1:
                connector_class = "completed" if step["completed"] else ""
                with cols[col_idx + 1]:
                    st.markdown(f'<div class="step-connector {connector_class}"></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_patient_info_step(self):
        """Render patient information input form"""
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span style="color: #3b82f6;">👤</span>
                Patient Information
            </h2>
            <p style="color: rgba(255, 255, 255, 0.7); margin: 0;">
                Please provide your basic information to get personalized medication advice
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Age input
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <label style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; font-weight: 500;">
                <span>📅</span>
                Age
            </label>
        </div>
        """, unsafe_allow_html=True)
        
        age = st.number_input(
            "Age",
            min_value=1,
            max_value=120,
            value=st.session_state.patient_info.age if st.session_state.patient_info else 25,
            key="age_input",
            label_visibility="collapsed"
        )
        
        # Gender selection
        st.markdown("""
        <div style="margin: 1.5rem 0;">
            <label style="font-weight: 500; margin-bottom: 1rem; display: block;">Gender</label>
        </div>
        """, unsafe_allow_html=True)
        
        # Gender radio buttons - only Male and Female
        current_gender = st.session_state.patient_info.gender if st.session_state.patient_info else "M"
        
        gender_options = ["Male", "Female"]
        gender_values = ["M", "F"]
        gender_icons = ["👨", "👩"]
        
        # Custom gender selection using columns
        col1, col2 = st.columns(2)
        
        selected_gender = current_gender if current_gender in gender_values else "M"
        for i, (col, option, value, icon) in enumerate(zip([col1, col2], gender_options, gender_values, gender_icons)):
            with col:
                button_style = """
                <div style="
                    background: rgba(59, 130, 246, 0.2); 
                    border: 2px solid #3b82f6; 
                    color: #3b82f6;
                    border-radius: 8px; 
                    padding: 1rem; 
                    text-align: center; 
                    cursor: pointer;
                    margin: 0.25rem 0;
                ">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{}</div>
                    <div style="font-weight: 500;">{}</div>
                </div>
                """.format(icon, option) if selected_gender == value else """
                <div style="
                    background: rgba(30, 41, 59, 0.8); 
                    border: 2px solid rgba(100, 116, 139, 0.4); 
                    color: white;
                    border-radius: 8px; 
                    padding: 1rem; 
                    text-align: center; 
                    cursor: pointer;
                    margin: 0.25rem 0;
                ">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{}</div>
                    <div style="font-weight: 500;">{}</div>
                </div>
                """.format(icon, option)
                
                st.markdown(button_style, unsafe_allow_html=True)
                
                if st.button(f"Select {option}", key=f"gender_btn_{value}", use_container_width=True):
                    selected_gender = value
                    # Update the session state immediately
                    if not st.session_state.patient_info:
                        st.session_state.patient_info = PatientInfo(age=25, gender=value)
                    else:
                        st.session_state.patient_info.gender = value
                    st.rerun()
        
        # Info box
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.8); border-radius: 8px; padding: 1rem; margin: 1.5rem 0; border-left: 4px solid #3b82f6;">
            <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                <span style="color: #3b82f6;">ℹ️</span>
                <div>
                    <div style="font-weight: 500; margin-bottom: 0.5rem;">Why we need this information:</div>
                    <ul style="margin: 0; padding-left: 1rem; font-size: 0.9rem; color: rgba(255, 255, 255, 0.8);">
                        <li>Age helps determine appropriate dosages and drug interactions</li>
                        <li>Gender affects medication metabolism and safety considerations</li>
                        <li>This information is used only for generating personalized advice</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "Continue to Medications →",
                use_container_width=True,
                type="primary",
                key="continue_to_meds"
            ):
                if 1 <= age <= 110:
                    st.session_state.patient_info = PatientInfo(age=age, gender=selected_gender)
                    st.session_state.current_step = 2
                    st.rerun()
                else:
                    st.error("Please enter a valid age between 1 and 110 years")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_medication_step(self):
        """Render medication input form"""
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span style="color: #3b82f6;">💊</span>
                Medication Details
            </h2>
            <p style="color: rgba(255, 255, 255, 0.7); margin: 0;">
                Add your medications and specify when you take them
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Patient summary
        if st.session_state.patient_info:
            patient = st.session_state.patient_info
            gender_text = {"M": "Male", "F": "Female"}[patient.gender]
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.8); border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem;">
                <div style="display: flex; align-items: center; gap: 1rem; font-size: 0.9rem;">
                    <span style="font-weight: 500;">Patient:</span>
                    <span>{patient.age} years old</span>
                    <span>•</span>
                    <span>{gender_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Initialize medications if empty
        if not st.session_state.medications:
            st.session_state.medications = [
                Medication(id="1", name="", morning=0, noon=0, night=0)
            ]
        
        # Render each medication
        for i, medication in enumerate(st.session_state.medications):
            st.markdown(f'<div class="medication-item">', unsafe_allow_html=True)
            
            # Medication header
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"<h4>Medication {i + 1}</h4>", unsafe_allow_html=True)
            
            with col2:
                if len(st.session_state.medications) > 1:
                    if st.button("🗑️", key=f"delete_{medication.id}", help="Remove medication"):
                        st.session_state.medications = [
                            med for med in st.session_state.medications if med.id != medication.id
                        ]
                        if medication.id in st.session_state.suggestions:
                            del st.session_state.suggestions[medication.id]
                        st.rerun()
            
            # Medication name input with search
            st.markdown("""
            <div style="margin: 1rem 0;">
                <label style="font-weight: 500; margin-bottom: 0.5rem; display: block;">Medication Name</label>
            </div>
            """, unsafe_allow_html=True)
            
            # Create a text input for medication name
            med_name = st.text_input(
                "Medication Name",
                value=medication.name,
                key=f"med_name_{medication.id}",
                placeholder="Type medication name...",
                label_visibility="collapsed"
            )
            
            # Update medication name in state if changed
            if med_name != medication.name:
                for j, med in enumerate(st.session_state.medications):
                    if med.id == medication.id:
                        st.session_state.medications[j] = Medication(
                            id=med.id,
                            name=med_name,
                            morning=med.morning,
                            noon=med.noon,
                            night=med.night
                        )
                        # Trigger search for suggestions
                        if len(med_name.strip()) >= 2:
                            self.search_drugs(med_name, medication.id)
                        break
            
            # Show suggestions if available
            if medication.id in st.session_state.suggestions and st.session_state.suggestions[medication.id]:
                st.markdown("**Suggestions:**")
                cols = st.columns(min(3, len(st.session_state.suggestions[medication.id])))
                for idx, suggestion in enumerate(st.session_state.suggestions[medication.id][:3]):
                    with cols[idx]:
                        if st.button(
                            f"✓ {suggestion}",
                            key=f"suggestion_{medication.id}_{suggestion}_{idx}",
                            help="Click to select this medication",
                            use_container_width=True
                        ):
                            # Update medication name
                            for j, med in enumerate(st.session_state.medications):
                                if med.id == medication.id:
                                    st.session_state.medications[j] = Medication(
                                        id=med.id,
                                        name=suggestion,
                                        morning=med.morning,
                                        noon=med.noon,
                                        night=med.night
                                    )
                                    break
                            # Clear suggestions
                            if medication.id in st.session_state.suggestions:
                                del st.session_state.suggestions[medication.id]
                            st.rerun()
            
            # Dosage schedule
            st.markdown("""
            <div style="margin: 1.5rem 0;">
                <label style="font-weight: 500; margin-bottom: 1rem; display: block;">Daily Schedule</label>
            </div>
            """, unsafe_allow_html=True)
            
            periods = [
                {"key": "morning", "label": "Morning", "icon": "🌅"},
                {"key": "noon", "label": "Noon", "icon": "☀️"},
                {"key": "night", "label": "Night", "icon": "🌙"}
            ]
            
            cols = st.columns(3)
            for col, period in zip(cols, periods):
                with col:
                    current_dose = getattr(medication, period["key"])
                    
                    st.markdown(f"""
                    <div class="dosage-item">
                        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{period["icon"]}</div>
                        <div style="font-weight: 500; margin-bottom: 1rem;">{period["label"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Dose controls
                    subcol1, subcol2, subcol3 = st.columns([1, 2, 1])
                    
                    # Decrease button
                    with subcol1:
                        button_disabled = current_dose <= 0
                        if st.button(
                            "−",
                            key=f"dec_{medication.id}_{period['key']}",
                            disabled=button_disabled,
                            help="Decrease dose",
                            use_container_width=True
                        ):
                            self.adjust_dose(medication.id, period["key"], False)
                    
                    # Dose value display
                    with subcol2:
                        st.markdown(f'<div class="dose-value">{current_dose}</div>', unsafe_allow_html=True)
                    
                    # Increase button  
                    with subcol3:
                        max_dose = self.dose_options[-1]
                        button_disabled = current_dose >= max_dose
                        if st.button(
                            "+",
                            key=f"inc_{medication.id}_{period['key']}",
                            disabled=button_disabled,
                            help="Increase dose",
                            use_container_width=True
                        ):
                            self.adjust_dose(medication.id, period["key"], True)
            
            # Schedule summary
            total_doses = medication.morning + medication.noon + medication.night
            if total_doses > 0:
                schedule_parts = []
                if medication.morning > 0:
                    schedule_parts.append(f"{medication.morning}")
                if medication.noon > 0:
                    schedule_parts.append(f"{medication.noon}")
                if medication.night > 0:
                    schedule_parts.append(f"{medication.night}")

                st.markdown(f"""
                <div style="background: rgba(59, 130, 246, 0.2); border-radius: 8px; padding: 1rem; margin-top: 1rem;">
                    <div style="font-weight: 500; color: #3b82f6; margin-bottom: 0.5rem;">Schedule Summary:</div>
                    <div style="color: rgba(255, 255, 255, 0.8);">{" ".join(schedule_parts)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Add medication button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➕ Add Another Medication", use_container_width=True, key="add_medication"):
                new_id = str(len(st.session_state.medications) + 1)
                st.session_state.medications.append(
                    Medication(id=new_id, name="", morning=0, noon=0, night=0)
                )
                st.rerun()
        
        # Validation and navigation
        valid_medications = [
            med for med in st.session_state.medications
            if med.name.strip() and (med.morning > 0 or med.noon > 0 or med.night > 0)
        ]
        
        if not valid_medications and any(med.name.strip() for med in st.session_state.medications):
            st.error("Please set at least one dose time for your medications")
        elif not any(med.name.strip() for med in st.session_state.medications):
            st.info("Please add at least one medication to continue")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back", use_container_width=True, key="back_to_patient"):
                st.session_state.current_step = 1
                st.rerun()
        
        with col2:
            if st.button("Start AI Consultation 🤖", use_container_width=True, type="primary", key="start_consultation"):
                if valid_medications:
                    st.session_state.medications = valid_medications
                    st.session_state.show_chat = True
                    st.session_state.current_step = 3
                    st.rerun()
                else:
                    st.error("Please add at least one valid medication")
        
        # Help text
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.8); border-radius: 8px; padding: 1rem; margin-top: 1.5rem; border-left: 4px solid #3b82f6;">
            <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                <span style="color: #3b82f6;">💡</span>
                <div>
                    <div style="font-weight: 500; margin-bottom: 0.5rem;">Dosage Tips:</div>
                    <ul style="margin: 0; padding-left: 1rem; font-size: 0.9rem; color: rgba(255, 255, 255, 0.8);">
                        <li>Use +/- buttons to adjust doses in 0.5 increments</li>
                        <li>1 = one tablet/pill, 0.5 = half tablet, etc.</li>
                        <li>Set doses to 0 for times when you don't take the medication</li>
                        <li>Search will suggest medications from our database</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def search_drugs(self, query: str, medication_id: str):
        """Search for drug suggestions"""
        if len(query) < 2:
            if medication_id in st.session_state.suggestions:
                del st.session_state.suggestions[medication_id]
            return
        
        st.session_state.loading_suggestions[medication_id] = True
        
        try:
            response = requests.get(
                f"{self.api_base_url}/search_drugs",
                params={"query": query, "limit": 5},
                timeout=10
            )
            if response.ok:
                data = response.json()
                st.session_state.suggestions[medication_id] = data.get("results", [])
            else:
                st.session_state.suggestions[medication_id] = []
        except:
            st.session_state.suggestions[medication_id] = []
        
        st.session_state.loading_suggestions[medication_id] = False
    
    def adjust_dose(self, med_id: str, period: str, increment: bool):
        """Adjust medication dose"""
        for i, med in enumerate(st.session_state.medications):
            if med.id == med_id:
                current_dose = getattr(med, period)
                try:
                    current_index = self.dose_options.index(current_dose)
                except ValueError:
                    current_index = 0
                
                if increment and current_index < len(self.dose_options) - 1:
                    new_dose = self.dose_options[current_index + 1]
                elif not increment and current_index > 0:
                    new_dose = self.dose_options[current_index - 1]
                else:
                    return
                
                # Update the medication
                new_med = Medication(
                    id=med.id,
                    name=med.name,
                    morning=new_dose if period == 'morning' else med.morning,
                    noon=new_dose if period == 'noon' else med.noon,
                    night=new_dose if period == 'night' else med.night
                )
                st.session_state.medications[i] = new_med
                st.rerun()
    
    def render_chat_interface(self):
        """Render chat interface for AI consultation"""
        # Create sidebar for patient summary
        with st.sidebar:
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.markdown("### 📋 Patient Summary")
            
            if st.session_state.patient_info:
                patient = st.session_state.patient_info
                st.write(f"**Age:** {patient.age} years")
                gender_map = {"M": "Male", "F": "Female"}
                st.write(f"**Gender:** {gender_map[patient.gender]}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.markdown("### 💊 Medications")
            
            for med in st.session_state.medications:
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.8); border-radius: 6px; padding: 0.75rem; margin: 0.5rem 0;">
                    <div style="font-weight: 500; margin-bottom: 0.25rem;">{med.name}</div>
                    <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.7);">
                        {med.morning} + {med.noon} + {med.night}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            if st.button("🔄 New Consultation", use_container_width=True):
                self.reset_flow()
            
            if st.session_state.advice_result:
                st.markdown("### � Download Report")
                self.download_advice()
        
        # Main chat area
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        
        st.markdown("""
        <h2 style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem;">
            <span style="color: #3b82f6;">💬</span>
            AI Medical Consultation
        </h2>
        """, unsafe_allow_html=True)
        
        if not st.session_state.chat_messages:
            # Initial consultation screen
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div style="text-align: center; padding: 3rem 1rem;">
                    <div style="width: 5rem; height: 5rem; background: rgba(59, 130, 246, 0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem;">
                        <span style="font-size: 2.5rem;">🤖</span>
                    </div>
                    <h3 style="margin-bottom: 1rem;">Ready for AI Consultation</h3>
                    <p style="color: rgba(255, 255, 255, 0.8); margin-bottom: 2rem;">
                        I'll analyze your medications and provide evidence-based guidance using 
                        medical literature and drug databases.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🚀 Start Consultation", use_container_width=True, type="primary"):
                    self.start_consultation()
        else:
            # Display chat messages
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            
            for message in st.session_state.chat_messages:
                if message["type"] == "user":
                    st.markdown(f"""
                    <div class="chat-message">
                        <div class="user-message">
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
                                <strong>👤 You</strong>
                            </div>
                            <div class="formatted-content" style="white-space: pre-wrap; line-height: 1.5;">{message["content"]}</div>
                            <div style="text-align: right; font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); margin-top: 0.8rem;">
                                {message["timestamp"]}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                elif message["type"] == "assistant":
                    # Use a simple container for the AI response header
                    st.markdown("""
                    <div style="margin: 1rem 0;">
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; background: rgba(16, 185, 129, 0.2); border: 1px solid rgba(16, 185, 129, 0.5); border-radius: 12px; padding: 1rem;">
                            <strong>🤖 AI Assistant</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display content using native streamlit markdown for better table rendering
                    st.markdown(message["content"])
                    
                    
                    # Show metadata if available
                    if "metadata" in message:
                        meta = message["metadata"]
                        st.markdown(f"""
                        <div class="message-metadata">
                            <div class="metadata-item">
                                <div style="font-weight: bold; font-size: 1.1rem;">{meta.get('medications_processed', 0)}</div>
                                <div>Medications Processed</div>
                            </div>
                            <div class="metadata-item">
                                <div style="font-weight: bold; font-size: 1.1rem;">{meta.get('medications_found', 0)}</div>
                                <div>Found in Database</div>
                            </div>
                            <div class="metadata-item">
                                <div style="font-weight: bold; font-size: 1.1rem;">{meta.get('pubmed_articles', 0)}</div>
                                <div>Research Articles</div>
                            </div>
                            <div class="metadata-item">
                                <div style="font-weight: bold; font-size: 1.1rem;">{meta.get('drug_interactions_found', 0)}</div>
                                <div>Interactions Found</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show research article references if available
                    if "references" in message and message["references"]:
                        st.markdown("""
                        <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                            <div style="font-weight: bold; margin-bottom: 1rem; color: #3b82f6;">📚 Research References:</div>
                        """, unsafe_allow_html=True)
                        
                        for i, ref in enumerate(message["references"][:5], 1):
                            # Extract title and URL from reference
                            if isinstance(ref, dict):
                                title = ref.get('title', f'Research Article {i}')
                                url = ref.get('url', '')
                                source = ref.get('source', 'Medical Literature')
                                year = ref.get('publication_year', '')
                                
                                # Clean up and format title
                                if not title or title.strip() == "":
                                    title = f"Medical Research Article {i}"
                                elif len(title) > 80:
                                    title = title[:77] + "..."
                                
                                # Add year to source if available
                                source_with_year = f"{source} ({year})" if year else source
                                
                            else:
                                # If it's a string, try to parse it
                                title = f"Medical Research Article {i}"
                                url = str(ref) if str(ref).startswith('http') else ''
                                source_with_year = "Medical Literature"
                            
                            # Validate and clean URL
                            is_valid_url = url and url.strip() and url.startswith(('http://', 'https://'))
                            clean_url = url.strip() if url else ''
                            
                            # Create reference box
                            st.markdown(f"""
                            <div style="background: rgba(30, 41, 59, 0.6); border-radius: 6px; padding: 0.75rem; margin: 0.5rem 0; border-left: 3px solid #3b82f6;">
                                <div style="font-weight: 500; margin-bottom: 0.5rem; color: #e2e8f0;">
                                    {i}. {title}
                                </div>
                                <div style="font-size: 0.75rem; color: rgba(255, 255, 255, 0.6); margin-bottom: 0.5rem;">
                                    📚 {source_with_year}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add clickable URL link if available
                            if is_valid_url:
                                st.markdown(f"""
                                <div style="margin: -0.25rem 0 0.5rem 0; padding-left: 0.75rem;">
                                    <a href="{clean_url}" target="_blank" rel="noopener noreferrer" 
                                       style="color: #60a5fa; text-decoration: none; font-size: 0.8rem; 
                                              display: inline-flex; align-items: center; gap: 0.25rem;
                                              border: 1px solid rgba(96, 165, 250, 0.3); 
                                              padding: 0.25rem 0.5rem; border-radius: 4px; 
                                              background: rgba(96, 165, 250, 0.1);
                                              transition: all 0.2s ease;"
                                       onmouseover="this.style.backgroundColor='rgba(96, 165, 250, 0.2)'; this.style.borderColor='rgba(96, 165, 250, 0.5)'"
                                       onmouseout="this.style.backgroundColor='rgba(96, 165, 250, 0.1)'; this.style.borderColor='rgba(96, 165, 250, 0.3)'"
                                       onclick="console.log('Clicking URL:', '{clean_url}'); window.open('{clean_url}', '_blank', 'noopener,noreferrer'); return false;">
                                        🔗 View Article
                                    </a>
                                    <div style="margin-top: 0.25rem; font-size: 0.7rem; color: rgba(255, 255, 255, 0.5); font-family: monospace;">
                                        {clean_url}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style="margin: -0.25rem 0 0.5rem 0; padding-left: 0.75rem;">
                                    <span style="color: #94a3b8; font-size: 0.8rem; font-style: italic;">
                                        � URL not available
                                    </span>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Add timestamp at the end
                    st.markdown(f"""
                    <div style="text-align: right; font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); margin: 1rem 0;">
                        Generated by AI • {message["timestamp"]}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Loading indicator
            if st.session_state.is_loading:
                st.markdown("""
                <div class="chat-message">
                    <div class="assistant-message">
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <strong>🤖 AI Assistant</strong>
                        </div>
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div class="loading-dots">
                                <div class="loading-dot"></div>
                                <div class="loading-dot"></div>
                                <div class="loading-dot"></div>
                            </div>
                            <span style="color: rgba(255, 255, 255, 0.8);">Analyzing medications and generating advice...</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Process consultation if loading
            if st.session_state.is_loading:
                self.process_consultation()
            
            # Add download section at bottom of chat when advice is available
            if st.session_state.advice_result and st.session_state.chat_messages:
                st.markdown("---")
                st.markdown("### 📋 Download Your Medical Advice Report")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    self.download_advice()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def start_consultation(self):
        """Start the AI consultation"""
        # Add user message
        user_message = self.format_user_summary()
        st.session_state.chat_messages.append({
            "type": "user",
            "content": user_message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Set loading state and rerun to show loading indicator
        st.session_state.is_loading = True
        st.rerun()
        
    def process_consultation(self):
        """Process the consultation request - called when loading is true"""
        try:
            # First check if API is available
            health_response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if health_response.status_code != 200:
                raise requests.exceptions.RequestException("API health check failed")
            
            # Call the advice API with progress
            advice_result = self.call_advice_api()
            st.session_state.advice_result = advice_result
            
            # Add assistant response
            references = []
            if "context_sources" in advice_result:
                for i, source in enumerate(advice_result["context_sources"][:5], 1):
                    if isinstance(source, dict):
                        # Extract from dictionary format (proper document structure)
                        title = source.get('title', f'Medical Research Article {i}')
                        url = source.get('url', '')
                        doc_source = source.get('source', 'Medical Literature')
                        year = source.get('publication_year', '')
                        
                        # Clean up title if it's too long
                        if len(title) > 100:
                            title = title[:97] + "..."
                        
                        # Ensure URL is valid or empty
                        clean_url = url.strip() if url and url.strip() and url.startswith(('http://', 'https://')) else ''
                        
                        references.append({
                            'title': title,
                            'url': clean_url,
                            'source': doc_source,
                            'publication_year': year
                        })
                    elif isinstance(source, str) and source:
                        # Handle string format
                        if source.startswith(('http://', 'https://')):
                            references.append({
                                'title': f'Medical Research Document {i}',
                                'url': source,
                                'source': 'PubMed/Medical Database',
                                'publication_year': ''
                            })
                        else:
                            # Assume it's a title or description
                            references.append({
                                'title': source[:100] + "..." if len(source) > 100 else source,
                                'url': '',
                                'source': 'Medical Literature',
                                'publication_year': ''
                            })
                    else:
                        # Fallback
                        references.append({
                            'title': f'Medical Research Article {i}',
                            'url': '',
                            'source': 'Medical Literature',
                            'publication_year': ''
                        })
            
            st.session_state.chat_messages.append({
                "type": "assistant",
                "content": advice_result["advice"],
                "metadata": {
                    "medications_processed": advice_result.get("medications_processed", 0),
                    "medications_found": advice_result.get("medications_found", 0),
                    "pubmed_articles": advice_result.get("pubmed_articles", 0),
                    "drug_interactions_found": advice_result.get("drug_interactions_found", 0)
                },
                "references": references,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
        except requests.exceptions.ConnectionError:
            st.session_state.chat_messages.append({
                "type": "assistant",
                "content": """❌ **Backend API Connection Error**
I'm unable to connect to the backend API server. This could mean:
""",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except requests.exceptions.Timeout:
            st.session_state.chat_messages.append({
                "type": "assistant",
                "content": "⏱️ **Request Timeout**: The API is taking too long to respond. This is normal for the first request as the AI model needs to load. Please try again in a moment.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            error_msg = str(e)
            if "Connection refused" in error_msg or "Failed to establish a new connection" in error_msg:
                st.session_state.chat_messages.append({
                    "type": "assistant",
                    "content": """❌ **Backend API Not Running**
The backend API server is not running. To use the AI consultation feature:
🚀 **Quick Start:**
1. Open a terminal in your project directory
2. Run: `./dev_start.sh` (this starts both API and frontend)
   
   OR manually start the API:
   `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. Wait for the API to load (it takes ~30 seconds to initialize)
4. Try the consultation again
The API provides access to medical literature, drug databases, and AI analysis for safe medication guidance.""",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                st.session_state.chat_messages.append({
                    "type": "assistant",
                    "content": f"❌ **Error**: {error_msg}\n\nPlease try again or consult with a healthcare professional if the issue persists.",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Always clear loading state
        st.session_state.is_loading = False
        st.rerun()
    
    def format_user_summary(self) -> str:
        """Format user information as a summary message"""
        patient = st.session_state.patient_info
        gender_text = {"M": "Male", "F": "Female"}[patient.gender]
        
        summary = f"Patient: {patient.age} years old, {gender_text}\n\nMedications:\n"
        
        for i, med in enumerate(st.session_state.medications, 1):
            summary += f"{i}. {med.name} - Schedule: {med.morning} + {med.noon} + {med.night}\n"

        return summary
    
    def call_advice_api(self) -> Dict:
        """Call the backend API to get medication advice"""
        url = f"{self.api_base_url}/advise"
        
        payload = {
            "meds": [med.name for med in st.session_state.medications],
            "schedule": [f"{med.morning}+{med.noon}+{med.night}" for med in st.session_state.medications],
            "age": st.session_state.patient_info.age,
            "gender": st.session_state.patient_info.gender
        }
        
        # Increase timeout for first request as AI model needs time to load
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        return response.json()
    
    def reset_flow(self):
        """Reset the entire flow to start over"""
        st.session_state.current_step = 1
        st.session_state.patient_info = None
        st.session_state.medications = []
        st.session_state.chat_messages = []
        st.session_state.show_chat = False
        st.session_state.advice_result = None
        st.session_state.is_loading = False
        st.session_state.suggestions = {}
        st.session_state.loading_suggestions = {}
        st.session_state.errors = {}
        st.rerun()
    
    def generate_pdf_report(self) -> bytes:
        """Generate a comprehensive PDF report of the medical advice"""
        if not st.session_state.advice_result:
            return None
        
        # Create a buffer to store the PDF
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1e40af')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#059669')
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.HexColor('#0369a1')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0
        )
        
        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            leftIndent=20,
            bulletIndent=10
        )
        
        # Build the story (content)
        story = []
        
        # Title
        story.append(Paragraph("🩺 Medical Advisor Report", title_style))
        story.append(Spacer(1, 20))
        
        # Patient Information
        if st.session_state.patient_info:
            patient = st.session_state.patient_info
            gender_text = {"M": "Male", "F": "Female"}[patient.gender]
            
            story.append(Paragraph("Patient Information", heading_style))
            
            patient_data = [
                ['Age:', f'{patient.age} years'],
                ['Gender:', gender_text],
                ['Report Date:', datetime.now().strftime("%B %d, %Y at %I:%M %p")]
            ]
            
            patient_table = Table(patient_data, colWidths=[2*inch, 3*inch])
            patient_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(patient_table)
            story.append(Spacer(1, 20))
        
        # Medications
        if st.session_state.medications:
            story.append(Paragraph("Current Medications", heading_style))
            
            for i, med in enumerate(st.session_state.medications, 1):
                if med.name.strip() and (med.morning > 0 or med.noon > 0 or med.night > 0):
                    story.append(Paragraph(f"{i}. {med.name}", subheading_style))
                    
                    schedule_parts = []
                    if med.morning > 0:
                        schedule_parts.append(f"Morning: {med.morning}")
                    if med.noon > 0:
                        schedule_parts.append(f"Noon: {med.noon}")
                    if med.night > 0:
                        schedule_parts.append(f"Night: {med.night}")
                    
                    schedule_text = " | ".join(schedule_parts)
                    total_daily = med.morning + med.noon + med.night
                    
                    story.append(Paragraph(f"Daily Schedule: {schedule_text}", normal_style))
                    story.append(Paragraph(f"Total Daily Dose: {total_daily}", normal_style))
                    story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 15))
        
        # Medical Advice
        story.append(Paragraph("AI Medical Advice", heading_style))
        
        # Get the raw advice content as displayed on the website
        advice_content = st.session_state.advice_result["advice"]
        
        # Process the content line by line to preserve markdown structure
        lines = advice_content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                story.append(Spacer(1, 6))
                i += 1
                continue
            
            # Handle headers
            if line.startswith('## '):
                header_text = line[3:].strip()
                story.append(Paragraph(header_text, heading_style))
                story.append(Spacer(1, 10))
            elif line.startswith('### '):
                subheader_text = line[4:].strip()
                story.append(Paragraph(subheader_text, subheading_style))
                story.append(Spacer(1, 8))
            elif line.startswith('# '):
                main_header_text = line[2:].strip()
                story.append(Paragraph(main_header_text, title_style))
                story.append(Spacer(1, 12))
            
            # Handle bullet points
            elif line.startswith('- ') or line.startswith('• '):
                bullet_text = line[2:].strip()
                story.append(Paragraph(f"• {bullet_text}", bullet_style))
                story.append(Spacer(1, 3))
            
            # Handle tables - look for markdown table format
            elif '|' in line and (i == 0 or not lines[i-1].strip() or '|' not in lines[i-1]):
                # Found start of a table
                table_lines = []
                j = i
                while j < len(lines) and '|' in lines[j]:
                    table_lines.append(lines[j].strip())
                    j += 1
                
                if len(table_lines) >= 2:  # At least header and separator
                    # Parse the table
                    table_data = []
                    for table_line in table_lines:
                        if table_line.startswith('|') and table_line.endswith('|'):
                            # Remove leading/trailing pipes and split
                            cells = [cell.strip() for cell in table_line[1:-1].split('|')]
                            # Skip separator lines (lines with only - and | characters)
                            if not all(c in '-|: ' for c in table_line):
                                table_data.append(cells)
                    
                    if table_data and len(table_data[0]) >= 2:
                        # Create PDF table
                        col_widths = [2.5*inch, 3*inch] if len(table_data[0]) == 2 else [A4[0] / len(table_data[0]) - 1*inch] * len(table_data[0])
                        
                        pdf_table = Table(table_data, colWidths=col_widths)
                        pdf_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ]))
                        story.append(pdf_table)
                        story.append(Spacer(1, 12))
                
                i = j  # Skip processed table lines
            
            # Handle regular paragraphs
            else:
                # Clean up the text and handle bold/italic
                text = line
                # Simple bold conversion
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                
                story.append(Paragraph(text, normal_style))
                story.append(Spacer(1, 4))
            
            i += 1
        
        # Metadata if available
        if "metadata" in st.session_state.chat_messages[-1]:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Analysis Summary", heading_style))
            
            meta = st.session_state.chat_messages[-1]["metadata"]
            meta_data = [
                ['Medications Processed:', str(meta.get('medications_processed', 0))],
                ['Found in Database:', str(meta.get('medications_found', 0))],
                ['Research Articles Reviewed:', str(meta.get('pubmed_articles', 0))],
                ['Drug Interactions Found:', str(meta.get('drug_interactions_found', 0))]
            ]
            
            meta_table = Table(meta_data, colWidths=[3*inch, 2*inch])
            meta_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(meta_table)
        
        # References if available
        if st.session_state.chat_messages and "references" in st.session_state.chat_messages[-1]:
            references = st.session_state.chat_messages[-1]["references"]
            if references:
                story.append(Spacer(1, 20))
                story.append(Paragraph("Research References", heading_style))
                
                for i, ref in enumerate(references[:5], 1):
                    if isinstance(ref, dict):
                        title = ref.get('title', f'Research Article {i}')
                        source = ref.get('source', 'Medical Literature')
                        year = ref.get('publication_year', '')
                        url = ref.get('url', '')
                        
                        ref_text = f"{i}. {title}"
                        if year:
                            ref_text += f" ({year})"
                        if source:
                            ref_text += f" - {source}"
                        if url and url != '#':
                            ref_text += f" - {source}"
                    else:
                        ref_text = f"{i}. {str(ref)}"
                    
                    story.append(Paragraph(ref_text, normal_style))
                    story.append(Spacer(1, 4))
        
        # Disclaimer
        story.append(Spacer(1, 30))
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#ef4444'),
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        story.append(Paragraph("⚠️ MEDICAL DISCLAIMER", disclaimer_style))
        story.append(Paragraph(
            "This report provides educational information only and is not a substitute for professional medical advice. "
            "Always consult with a qualified healthcare provider for medical decisions. The AI-generated advice should "
            "be reviewed with your doctor before making any changes to your medication regimen.",
            disclaimer_style
        ))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF data
        buffer.seek(0)
        return buffer.getvalue()

    def download_advice(self):
        """Download the advice as text or PDF file"""
        if st.session_state.advice_result:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create two columns for download options
            col1, col2 = st.columns(2)
            
            with col1:
                # Text download
                advice_text = self.clean_and_format_content(st.session_state.advice_result["advice"])
                
                # Create comprehensive text report
                text_report = self.create_text_report(advice_text, timestamp)
                
                st.download_button(
                    label="📄 Download as Text",
                    data=text_report,
                    file_name=f"medication_advice_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # PDF download
                try:
                    pdf_data = self.generate_pdf_report()
                    if pdf_data:
                        st.download_button(
                            label="📋 Download as PDF",
                            data=pdf_data,
                            file_name=f"medication_advice_{timestamp}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    else:
                        st.error("Failed to generate PDF")
                except Exception as e:
                    st.error(f"PDF generation error: {str(e)}")
    
    def create_text_report(self, advice_content: str, timestamp: str) -> str:
        """Create a comprehensive text report"""
        report_lines = []
        
        # Header
        report_lines.append("=" * 70)
        report_lines.append("MEDICAL ADVISOR REPORT")
        report_lines.append("=" * 70)
        report_lines.append(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        report_lines.append("")
        
        # Patient Information
        if st.session_state.patient_info:
            patient = st.session_state.patient_info
            gender_text = {"M": "Male", "F": "Female"}[patient.gender]
            
            report_lines.append("PATIENT INFORMATION")
            report_lines.append("-" * 20)
            report_lines.append(f"Age: {patient.age} years")
            report_lines.append(f"Gender: {gender_text}")
            report_lines.append("")
        
        # Medications
        if st.session_state.medications:
            report_lines.append("CURRENT MEDICATIONS")
            report_lines.append("-" * 20)
            
            for i, med in enumerate(st.session_state.medications, 1):
                if med.name.strip() and (med.morning > 0 or med.noon > 0 or med.night > 0):
                    report_lines.append(f"{i}. {med.name}")
                    
                    schedule_parts = []
                    if med.morning > 0:
                        schedule_parts.append(f"Morning: {med.morning}")
                    if med.noon > 0:
                        schedule_parts.append(f"Noon: {med.noon}")
                    if med.night > 0:
                        schedule_parts.append(f"Night: {med.night}")
                    
                    schedule_text = " | ".join(schedule_parts)
                    total_daily = med.morning + med.noon + med.night
                    
                    report_lines.append(f"   Daily Schedule: {schedule_text}")
                    report_lines.append(f"   Total Daily Dose: {total_daily}")
                    report_lines.append("")
        
        # Medical Advice
        report_lines.append("AI MEDICAL ADVICE")
        report_lines.append("-" * 20)
        report_lines.append(advice_content)
        report_lines.append("")
        
        # Metadata
        if st.session_state.chat_messages and "metadata" in st.session_state.chat_messages[-1]:
            meta = st.session_state.chat_messages[-1]["metadata"]
            report_lines.append("ANALYSIS SUMMARY")
            report_lines.append("-" * 20)
            report_lines.append(f"Medications Processed: {meta.get('medications_processed', 0)}")
            report_lines.append(f"Found in Database: {meta.get('medications_found', 0)}")
            report_lines.append(f"Research Articles Reviewed: {meta.get('pubmed_articles', 0)}")
            report_lines.append(f"Drug Interactions Found: {meta.get('drug_interactions_found', 0)}")
            report_lines.append("")
        
        # References
        if st.session_state.chat_messages and "references" in st.session_state.chat_messages[-1]:
            references = st.session_state.chat_messages[-1]["references"]
            if references:
                report_lines.append("RESEARCH REFERENCES")
                report_lines.append("-" * 20)
                
                for i, ref in enumerate(references[:5], 1):
                    if isinstance(ref, dict):
                        title = ref.get('title', f'Research Article {i}')
                        source = ref.get('source', 'Medical Literature')
                        year = ref.get('publication_year', '')
                        url = ref.get('url', '')
                        
                        ref_text = f"{i}. {title}"
                        if year:
                            ref_text += f" ({year})"
                        if source:
                            ref_text += f" - {source}"
                        if url and url != '#':
                            ref_text += f"\n   URL: {url}"
                    else:
                        ref_text = f"{i}. {str(ref)}"
                    
                    report_lines.append(ref_text)
                    report_lines.append("")
        
        # Disclaimer
        report_lines.append("=" * 70)
        report_lines.append("MEDICAL DISCLAIMER")
        report_lines.append("=" * 70)
        report_lines.append("This report provides educational information only and is not a substitute")
        report_lines.append("for professional medical advice. Always consult with a qualified healthcare")
        report_lines.append("provider for medical decisions. The AI-generated advice should be reviewed")
        report_lines.append("with your doctor before making any changes to your medication regimen.")
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)
    
    def render_disclaimer(self):
        """Render medical disclaimer with compact styling"""
        st.markdown("""
        <div class="compact-disclaimer">
            <strong>⚠️ Medical Disclaimer:</strong> This tool provides educational information only 
            and is not a substitute for professional medical advice. Always consult with a qualified 
            healthcare provider for medical decisions.
        </div>
        """, unsafe_allow_html=True)
    
    def run(self):
        """Main application entry point"""
        # Render header
        self.render_header()
        
        # Main content container with compact spacing
        st.markdown('<div style="max-width: 1200px; margin: 0 auto; padding: 0 0.5rem;">', unsafe_allow_html=True)
        
        # Show step indicator only if not in chat mode
        if not st.session_state.show_chat:
            self.render_step_indicator()
            
            # Render appropriate step
            if st.session_state.current_step == 1:
                self.render_patient_info_step()
            elif st.session_state.current_step == 2:
                self.render_medication_step()
        else:
            # Show chat interface
            self.render_chat_interface()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Render disclaimer
        self.render_disclaimer()

# Run the application
if __name__ == "__main__":
    app = MedicalAdvisorApp()
    app.run()
