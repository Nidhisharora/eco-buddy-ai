"""
UI renderer for Carbon Handprint Metrics.
"""

from typing import Dict, Any

def render_handprint_card(result: Dict[str, Any]) -> str:
    """
    Renders positive carbon handprint metric card in HTML/CSS.
    """
    return f"""
    <div style="border: 1px solid #16a34a; border-radius: 8px; padding: 16px; background-color: #f0fdf4;">
        <h4 style="margin: 0 0 10px 0; color: #15803d;">✋ Positive Carbon Handprint Impact</h4>
        <div style="display: flex; gap: 20px; font-size: 0.95em;">
            <div><strong>Direct Avoided Carbon:</strong> {result['direct_avoided_carbon_kg']} kg CO2</div>
            <div><strong>Ripple Multiplier:</strong> {result['indirect_handprint_multiplier']}x</div>
            <div><strong>Total Handprint:</strong> {result['total_handprint_impact_kg']} kg CO2</div>
        </div>
    </div>
    """
