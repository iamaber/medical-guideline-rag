"""HTML formatter for structured medication advice.

This module provides utility functions to format structured medication advice
into styled HTML responses for web display.

Usage:
    from src.utils.html_formatter import format_advice_to_html
    from src.models.medication_advice import StructuredMedicationAdvice

    advice = StructuredMedicationAdvice(...)
    html = format_advice_to_html(advice)
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.models.medication_advice import (
    StructuredMedicationAdvice,
    DrugInteraction,
    DosDontsPair,
)

logger = logging.getLogger(__name__)

# HTML template with modern styling
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medication Guidance Report</title>
    <style>
        /* Modern CSS variables */
        :root {{
            --primary: #0ea5e9;
            --primary-dark: #0284c7;
            --success: #10b981;
            --success-dark: #059669;
            --warning: #f59e0b;
            --warning-dark: #d97706;
            --error: #f43f5e;
            --error-dark: #dc2626;
            --neutral: #64748b;
            --neutral-dark: #475569;
            --surface: #ffffff;
            --surface-alt: #f8fafc;
            --border: #e2e8f0;
        }}

        /* Base styles */
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: #0f172a;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #f1f5f9;
        }}

        .container {{
            background: var(--surface);
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }}

        /* Headings */
        h1 {{
            color: var(--primary-dark);
            border-bottom: 3px solid var(--primary);
            padding-bottom: 16px;
            margin-bottom: 24px;
            font-size: 32px;
            font-weight: 700;
        }}

        h2 {{
            color: var(--neutral-dark);
            margin-top: 32px;
            margin-bottom: 16px;
            font-size: 24px;
            font-weight: 600;
        }}

        h3 {{
            color: var(--neutral);
            margin-top: 24px;
            margin-bottom: 12px;
            font-size: 20px;
            font-weight: 500;
        }}

        /* Interaction alerts */
        .interaction-alert {{
            border-left: 4px solid var(--error);
            background: linear-gradient(90deg, #fef2f2 0%, #fee2e2 100%);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}

        .interaction-alert.severe {{
            border-left-color: var(--error-dark);
            background: linear-gradient(90deg, #fef2f2 0%, #fecaca 100%);
        }}

        .interaction-alert.major {{
            border-left-color: #ea580c;
            background: linear-gradient(90deg, #fff7ed 0%, #ffedd5 100%);
        }}

        .interaction-alert.moderate {{
            border-left-color: var(--warning);
            background: linear-gradient(90deg, #fffbeb 0%, #fef3c7 100%);
        }}

        /* Dos and Don'ts table */
        .dos-donts-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border-radius: 8px;
            overflow: hidden;
        }}

        .dos-donts-table th {{
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            color: white;
            padding: 18px;
            text-align: center;
            font-size: 18px;
            font-weight: 600;
        }}

        .dos-donts-table td {{
            padding: 16px;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
            font-size: 15px;
        }}

        .dont-column {{
            background-color: #fff5f5;
            border-left: 4px solid var(--error);
        }}

        .do-column {{
            background-color: #f0fff4;
            border-left: 4px solid var(--success);
        }}

        .dos-donts-table tr:hover {{
            background-color: #e8f4f8;
        }}

        /* Info cards */
        .info-card {{
            background-color: var(--surface-alt);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid var(--primary);
            margin: 16px 0;
        }}

        .info-card.warning {{
            border-left-color: var(--warning);
            background-color: #fffbeb;
        }}

        .info-card.success {{
            border-left-color: var(--success);
            background-color: #f0fdf4;
        }}

        /* Lists */
        ul {{
            padding-left: 24px;
            margin: 12px 0;
        }}

        li {{
            margin-bottom: 8px;
            line-height: 1.7;
        }}

        /* Medication list */
        .medication-list {{
            background: linear-gradient(90deg, #f0fff4 0%, #dcfce7 100%);
            padding: 20px;
            border-radius: 8px;
            margin: 16px 0;
            border: 2px solid var(--success-dark);
        }}

        /* Badge */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge.severe {{
            background-color: var(--error);
            color: white;
        }}

        .badge.major {{
            background-color: #ea580c;
            color: white;
        }}

        .badge.moderate {{
            background-color: var(--warning);
            color: white;
        }}

        .badge.minor {{
            background-color: var(--primary);
            color: white;
        }}

        /* Footer */
        .footer {{
            margin-top: 48px;
            padding-top: 24px;
            border-top: 2px solid var(--border);
            text-align: center;
            color: var(--neutral);
            font-size: 14px;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            body {{
                padding: 20px 10px;
            }}

            .container {{
                padding: 20px;
            }}

            h1 {{
                font-size: 24px;
            }}

            h2 {{
                font-size: 20px;
            }}

            .dos-donts-table th,
            .dos-donts-table td {{
                padding: 12px 8px;
                font-size: 14px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 Medication Guidance Report</h1>
        {content}
        <div class="footer">
            <p><strong>Medical Disclaimer:</strong> This information is for educational purposes only.
            It is not a substitute for professional medical advice, diagnosis, or treatment.
            Always consult your healthcare provider before making any changes to your medication regimen.</p>
            <p style="margin-top: 8px;">Generated on {timestamp}</p>
        </div>
    </div>
</body>
</html>"""


def format_advice_to_html(advice: StructuredMedicationAdvice) -> str:
    """Format structured medication advice to styled HTML.

    Args:
        advice: Structured medication advice with all sections

    Returns:
        Complete HTML document as string
    """
    try:
        content_parts = []

        # Interaction warnings (PROMINENT - show first)
        if advice.drug_interactions:
            content_parts.append(_build_interactions_section(advice.drug_interactions))

        # Therapeutic indications
        if advice.therapeutic_indications:
            content_parts.append(_build_indications_section(advice.therapeutic_indications))

        # Regimen analysis
        if advice.regimen_analysis:
            content_parts.append(_build_regimen_section(advice.regimen_analysis))

        # Dosing strategy
        if advice.dosing_strategy:
            content_parts.append(_build_dosing_section(advice.dosing_strategy))

        # Dos and Don'ts table
        if advice.dos_and_donts:
            content_parts.append(_build_dos_donts_table(advice.dos_and_donts))

        # Safety monitoring
        if advice.safety_monitoring:
            content_parts.append(_build_monitoring_section(advice.safety_monitoring))

        # Lifestyle recommendations
        if advice.lifestyle_recommendations:
            content_parts.append(_build_lifestyle_section(advice.lifestyle_recommendations))

        # Emergency protocols
        if advice.emergency_protocols:
            content_parts.append(_build_emergency_section(advice.emergency_protocols))

        content = "\n".join(content_parts)
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        return HTML_TEMPLATE.format(content=content, timestamp=timestamp)

    except Exception as e:
        logger.error(f"Error formatting advice to HTML: {e}", exc_info=True)
        return f"<html><body><h1>Error formatting report</h1><p>{str(e)}</p></body></html>"


def _build_interactions_section(interactions: List[DrugInteraction]) -> str:
    """Build interactions section HTML.

    Args:
        interactions: List of drug interactions

    Returns:
        HTML string for interactions section
    """
    severity_order = {"severe": 0, "major": 1, "moderate": 2, "minor": 3}
    sorted_interactions = sorted(
        interactions, key=lambda x: severity_order.get(x.risk_level.lower(), 4)
    )

    html_parts = [
        '<h2>⚠️ Drug Interaction Warnings</h2>',
    ]

    for interaction in sorted_interactions:
        alert_class = interaction.risk_level.lower()
        html_parts.append(f"""
        <div class="interaction-alert {alert_class}">
            <h3>{', '.join(interaction.medications)}</h3>
            <span class="badge {alert_class}">{interaction.risk_level.upper()} RISK</span>
            <p style="margin-top: 12px;"><strong>Description:</strong> {interaction.description}</p>
            {f'<p><strong>Mechanism:</strong> {interaction.mitigation}</p>' if interaction.mitigation else ''}
        </div>
        """)

    return "\n".join(html_parts)


def _build_indications_section(indications: List) -> str:
    """Build therapeutic indications section HTML.

    Args:
        indications: List of therapeutic indications

    Returns:
        HTML string for indications section
    """
    if not indications:
        return ""

    html_parts = ['<h2>💊 Therapeutic Indications</h2>']

    for ind in indications:
        html_parts.append(f"""
        <div class="info-card">
            <h3>{ind.get('medication_name', 'Unknown Medication')}</h3>
            <p><strong>Indication:</strong> {ind.get('indication', 'N/A')}</p>
            <p><strong>Mechanism:</strong> {ind.get('mechanism', 'N/A')}</p>
        </div>
        """)

    return "\n".join(html_parts)


def _build_regimen_section(analysis: Dict) -> str:
    """Build regimen analysis section HTML.

    Args:
        analysis: Regimen analysis dictionary

    Returns:
        HTML string for regimen section
    """
    if not analysis:
        return ""

    return f"""
    <h2>📋 Regimen Analysis</h2>
    <div class="info-card">
        <p><strong>Therapeutic Purpose:</strong> {analysis.get('therapeutic_purpose', 'N/A')}</p>
        <p><strong>Key Interaction:</strong> {analysis.get('key_interaction', 'None identified')}</p>
        <p><strong>Timing Benefit:</strong> {analysis.get('timing_benefit', 'N/A')}</p>
    </div>
    """


def _build_dosing_section(strategy: Dict) -> str:
    """Build dosing strategy section HTML.

    Args:
        strategy: Dosing strategy dictionary

    Returns:
        HTML string for dosing section
    """
    if not strategy:
        return ""

    html_parts = ['<h2>⏰ Dosing Strategy</h2>']

    timing = strategy.get('timing_coordination', '')
    if timing:
        html_parts.append(f'<div class="info-card"><p><strong>Timing:</strong> {timing}</p></div>')

    guidelines = strategy.get('administration_guidelines', '')
    if guidelines:
        html_parts.append(f'<div class="info-card"><p><strong>Administration:</strong> {guidelines}</p></div>')

    food = strategy.get('food_interactions')
    if food:
        html_parts.append(f'<div class="info-card warning"><p><strong>Food Considerations:</strong> {food}</p></div>')

    return "\n".join(html_parts)


def _build_dos_donts_table(dos_donts: List[DosDontsPair]) -> str:
    """Build dos and don'ts table HTML.

    Args:
        dos_donts: List of do/don't pairs

    Returns:
        HTML string for dos/donts table
    """
    if not dos_donts:
        return ""

    html_parts = [
        '<h2>✅ Do\'s and ❌ Don\'ts</h2>',
        '<table class="dos-donts-table">',
        '<thead>',
        '<tr>',
        '<th style="width: 50%;">DON\'T</th>',
        '<th style="width: 50%;">DO</th>',
        '</tr>',
        '</thead>',
        '<tbody>',
    ]

    for pair in dos_donts:
        html_parts.append('<tr>')
        html_parts.append(f'<td class="dont-column"><p><strong>{pair.dont.text}</strong></p>')
        if pair.dont.category:
            html_parts.append(f'<span class="badge" style="margin-top: 8px;">{pair.dont.category}</span>')
        html_parts.append('</td>')

        html_parts.append(f'<td class="do-column"><p><strong>{pair.do.text}</strong></p>')
        if pair.do.category:
            html_parts.append(f'<span class="badge" style="margin-top: 8px;">{pair.do.category}</span>')
        html_parts.append('</td>')

        html_parts.append('</tr>')

    html_parts.extend(['</tbody>', '</table>'])
    return "\n".join(html_parts)


def _build_monitoring_section(monitoring: Dict) -> str:
    """Build safety monitoring section HTML.

    Args:
        monitoring: Safety monitoring dictionary

    Returns:
        HTML string for monitoring section
    """
    if not monitoring:
        return ""

    html_parts = ['<h2>🔬 Safety Monitoring</h2>']

    key_params = monitoring.get('key_parameters', [])
    if key_params:
        html_parts.append('<div class="medication-list">')
        html_parts.append('<h3>Parameters to Monitor:</h3>')
        html_parts.append('<ul>')
        for param in key_params:
            html_parts.append(f"""
            <li>
                <strong>{param.get('parameter', 'Unknown')}</strong> - {param.get('frequency', 'As needed')}
                {f"({param.get('normal_range', 'N/A')})" if param.get('normal_range') else ''}
            </li>
            """)
        html_parts.append('</ul>')
        html_parts.append('</div>')

    warning_signs = monitoring.get('warning_signs', [])
    if warning_signs:
        html_parts.append('<div class="info-card warning">')
        html_parts.append('<h3>⚠️ Warning Signs:</h3>')
        html_parts.append('<ul>')
        for sign in warning_signs:
            html_parts.append(f'<li>{sign}</li>')
        html_parts.append('</ul>')
        html_parts.append('</div>')

    return "\n".join(html_parts)


def _build_lifestyle_section(recommendations: List[Dict]) -> str:
    """Build lifestyle recommendations section HTML.

    Args:
        recommendations: List of lifestyle recommendations

    Returns:
        HTML string for lifestyle section
    """
    if not recommendations:
        return ""

    html_parts = ['<h2>🥗 Lifestyle Recommendations</h2>']

    for rec in recommendations:
        html_parts.append(f"""
        <div class="info-card success">
            <h3>{rec.get('category', 'Recommendation')}</h3>
            <p><strong>Recommendation:</strong> {rec.get('recommendation', 'N/A')}</p>
            <p style="color: var(--neutral);"><strong>Rationale:</strong> {rec.get('rationale', '')}</p>
        </div>
        """)

    return "\n".join(html_parts)


def _build_emergency_section(protocols: Optional[List[str]]) -> str:
    """Build emergency protocols section HTML.

    Args:
        protocols: List of emergency protocols

    Returns:
        HTML string for emergency section
    """
    if not protocols:
        return ""

    html_parts = [
        '<h2>🚨 Emergency Protocols</h2>',
        '<div class="info-card" style="border-left-color: var(--error); background: #fef2f2;">',
        '<ul>',
    ]

    for protocol in protocols:
        html_parts.append(f'<li>{protocol}</li>')

    html_parts.extend(['</ul>', '</div>'])
    return "\n".join(html_parts)
