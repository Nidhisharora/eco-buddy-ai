"""
Advocacy Campaign Generator.
Maps user footprint hotspots to relevant local or national policy issues and generates targeted advocacy campaigns.
"""

from typing import Dict, Any, List


class AdvocacyCampaignGenerator:
    """Generates personalized climate advocacy campaigns based on user emission hotspots."""

    # Mock mapping of emission hotspots to policy issues and campaigns
    HOTSPOT_MAPPING = {
        "high_aviation": {
            "policy_issue": "Sustainable Aviation Fuel (SAF) mandates and high-speed rail investment.",
            "campaigns": [
                {
                    "name": "Support the SAF Mandate Act",
                    "action_type": "email_representative",
                    "target": "National Legislature",
                    "template": "Dear [Representative], I urge you to support legislation mandating Sustainable Aviation Fuel blending to reduce the carbon footprint of air travel.",
                },
                {
                    "name": "Fund High-Speed Rail",
                    "action_type": "sign_petition",
                    "target": "Department of Transportation",
                    "template": "I petition for increased federal funding for high-speed rail to provide low-carbon alternatives to short-haul flights.",
                },
            ],
        },
        "high_home_energy": {
            "policy_issue": "Building electrification mandates and home weatherization subsidies.",
            "campaigns": [
                {
                    "name": "Expand Home Weatherization Assistance",
                    "action_type": "email_representative",
                    "target": "Local City Council",
                    "template": "Dear Council Member, I support expanding the local home weatherization assistance program to help low-income households reduce energy waste.",
                },
                {
                    "name": "Ban New Natural Gas Hookups",
                    "action_type": "attend_town_hall",
                    "target": "Zoning Board",
                    "template": "I will attend the upcoming town hall to speak in favor of phasing out new natural gas hookups in residential construction.",
                },
            ],
        },
        "high_diet_meat": {
            "policy_issue": "Agricultural subsidies reform and plant-based food accessibility.",
            "campaigns": [
                {
                    "name": "Shift Subsidies to Regenerative Ag",
                    "action_type": "email_representative",
                    "target": "Agricultural Committee",
                    "template": "Dear Representative, I urge you to support shifting agricultural subsidies away from industrial meat production toward regenerative, plant-based farming.",
                }
            ],
        },
        "high_vehicle": {
            "policy_issue": "Public transit expansion and EV charging infrastructure.",
            "campaigns": [
                {
                    "name": "Fund Local Bus Rapid Transit",
                    "action_type": "sign_petition",
                    "target": "Regional Transit Authority",
                    "template": "I petition the RTA to prioritize funding for Bus Rapid Transit corridors to provide reliable, low-carbon public transportation.",
                }
            ],
        },
    }

    def __init__(self, user_hotspots: List[str]):
        """
        Args:
            user_hotspots: List of user's top emission categories (e.g., ["high_aviation", "high_vehicle"]).
        """
        self.hotspots = [h.lower() for h in user_hotspots]

    def generate_personalized_campaigns(self) -> List[Dict[str, Any]]:
        """Generates a list of relevant campaigns based on user hotspots."""
        recommended_campaigns = []

        for hotspot in self.hotspots:
            if hotspot in self.HOTSPOT_MAPPING:
                mapping = self.HOTSPOT_MAPPING[hotspot]
                for campaign in mapping["campaigns"]:
                    recommended_campaigns.append(
                        {
                            "hotspot": hotspot.replace("_", " ").title(),
                            "policy_issue": mapping["policy_issue"],
                            **campaign,
                        }
                    )

        return recommended_campaigns

    def get_civic_impact_multiplier(self, action_type: str) -> float:
        """Returns a mock multiplier for the 'Civic Impact' score based on action effort."""
        multipliers = {
            "sign_petition": 1.0,
            "email_representative": 2.5,
            "attend_town_hall": 5.0,
            "volunteer_canvass": 10.0,
        }
        return multipliers.get(action_type.lower(), 1.0)
