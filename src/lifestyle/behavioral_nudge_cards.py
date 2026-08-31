"""
Streamlit UI cards for rendering behavioral nudges.
"""

from typing import List, Dict, Any

def render_nudge_cards(nudges: List[Dict[str, Any]]) -> None:
    """
    Renders behavioral nudges in HTML/CSS cards inside Streamlit or generic UI handlers.
    """
    if not nudges:
        return

    cards_html = ""
    for nudge in nudges:
        badge_color = "#e74c3c" if nudge["framing"] == "loss_aversion" else "#3498db"
        cards_html += f"""
        <div style="border: 1px solid #ddd; border-left: 5px solid {badge_color}; border-radius: 8px; padding: 16px; margin-bottom: 12px; background-color: #f9f9f9;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: bold; font-size: 1.1em; color: #2c3e50;">{nudge['headline']}</span>
                <span style="background-color: {badge_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; text-transform: uppercase;">{nudge['framing']}</span>
            </div>
            <p style="margin: 8px 0; color: #555;">{nudge['message']}</p>
            <div style="font-size: 0.9em; color: #27ae60; font-weight: 500;">
                🌱 Potential Impact: Save {nudge['potential_carbon_saving_kg']} kg CO2 / ${nudge['potential_cost_saving_usd']} per week
            </div>
        </div>
        """
    return cards_html
