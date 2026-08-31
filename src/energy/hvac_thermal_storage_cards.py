"""
UI rendering card for HVAC Thermal Storage Optimization schedule.
"""

from typing import Dict, Any

def render_hvac_schedule_summary(summary: Dict[str, Any]) -> str:
    """
    Renders thermal storage optimization summary widget in HTML/CSS.
    """
    return f"""
    <div style="border: 1px solid #27ae60; border-radius: 8px; padding: 16px; background-color: #f0fdf4;">
        <h4 style="margin: 0 0 10px 0; color: #166534;">❄️ HVAC Thermal Storage & Pre-Cooling Summary</h4>
        <div style="display: flex; gap: 20px;">
            <div><strong>Daily Energy Cost:</strong> ${summary['total_daily_cost_usd']}</div>
            <div><strong>Daily Carbon Emissions:</strong> {summary['total_daily_carbon_kg']} kg CO2</div>
            <div><strong>Peak Shaving Impact:</strong> {summary['peak_shaving_percentage']}%</div>
        </div>
    </div>
    """
