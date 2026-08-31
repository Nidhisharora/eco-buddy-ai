"""
UI renderer for Waste Stream Routing Results.
"""

from typing import Dict, Any

def render_waste_routing_card(result: Dict[str, Any]) -> str:
    """
    Renders circular waste routing decision card in HTML/CSS.
    """
    dest = result["best_destination"]
    return f"""
    <div style="border: 1px solid #854d0e; border-radius: 8px; padding: 16px; background-color: #fefce8;">
        <h4 style="margin: 0 0 10px 0; color: #713f12;">♻️ Waste Diversion Route: {dest['facility_name']}</h4>
        <div style="display: flex; gap: 20px; font-size: 0.95em;">
            <div><strong>Processing:</strong> {dest['processing_type'].capitalize()}</div>
            <div><strong>Net Carbon Benefit:</strong> {result['net_carbon_benefit_kg']} kg CO2</div>
            <div><strong>Estimated Payout:</strong> ${result['expected_payout_usd']}</div>
        </div>
    </div>
    """
