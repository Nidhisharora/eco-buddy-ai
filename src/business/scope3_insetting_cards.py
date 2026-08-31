"""
UI card renderer for Scope 3 Insetting Portfolio Summary.
"""

from typing import Dict, Any

def render_insetting_portfolio_summary(result: Dict[str, Any]) -> str:
    """
    Renders corporate insetting portfolio optimization widget in HTML/CSS.
    """
    return f"""
    <div style="border: 1px solid #0284c7; border-radius: 8px; padding: 16px; background-color: #f0f9ff;">
        <h4 style="margin: 0 0 10px 0; color: #0369a1;">🏢 Scope 3 Supply Chain Insetting Portfolio</h4>
        <div style="display: flex; gap: 20px; font-size: 0.95em;">
            <div><strong>Allocated Budget:</strong> ${result['total_budget_allocated_usd']}</div>
            <div><strong>Annual Abatement:</strong> {result['total_annual_abatement_tco2e']} tCO2e</div>
            <div><strong>Target Completion:</strong> {result['target_completion_percentage']}%</div>
        </div>
    </div>
    """
