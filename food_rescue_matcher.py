"""
Food Rescue Matcher.
Manages a mock network of surplus food donors and recipient organizations, matching based on item types, capacity, and spoilage timelines.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta


class FoodRescueMatcher:
    """Facilitates matching between food donors and community recipients."""

    # Mock recipient organizations
    RECIPIENTS = {
        "downtown_food_bank": {
            "name": "Downtown Community Food Bank",
            "capacity_kg": 500.0,
            "accepted_types": ["produce", "canned", "dairy", "bakery"],
            "dietary_restrictions": ["none"],
            "location": "Downtown",
        },
        "westside_shelter": {
            "name": "Westside Family Shelter",
            "capacity_kg": 200.0,
            "accepted_types": ["produce", "canned", "bakery"],
            "dietary_restrictions": ["no_pork", "no_alcohol"],
            "location": "Westside",
        },
        "university_fridge": {
            "name": "University Community Fridge",
            "capacity_kg": 100.0,
            "accepted_types": ["produce", "bakery", "prepared_meals"],
            "dietary_restrictions": ["vegetarian_only"],
            "location": "University District",
        },
    }

    def __init__(self):
        self.recipients = self.RECIPIENTS
        self.active_donations: List[Dict[str, Any]] = []

    def register_donation(
        self, donor_name: str, item_type: str, weight_kg: float, spoilage_hours: float
    ) -> str:
        """Registers a new surplus food donation."""
        donation_id = f"don_{len(self.active_donations) + 1}"
        expiry_time = datetime.now() + timedelta(hours=spoilage_hours)

        donation = {
            "id": donation_id,
            "donor_name": donor_name,
            "item_type": item_type.lower(),
            "weight_kg": weight_kg,
            "spoilage_hours": spoilage_hours,
            "expiry_time": expiry_time,
            "status": "pending",
            "matched_recipient": None,
        }

        self.active_donations.append(donation)
        return donation_id

    def find_best_match(self, donation_id: str) -> Dict[str, Any]:
        """Finds the best recipient for a specific donation."""
        donation = next(
            (d for d in self.active_donations if d["id"] == donation_id), None
        )
        if not donation or donation["status"] != "pending":
            return {"error": "Invalid or already matched donation."}

        potential_matches = []
        for rec_id, rec_details in self.recipients.items():
            # Check capacity
            if donation["weight_kg"] > rec_details["capacity_kg"]:
                continue

            # Check item type acceptance
            if donation["item_type"] not in rec_details["accepted_types"]:
                continue

            # Simple scoring: prefer closer location (mocked as exact match) or higher capacity remaining
            # For this mock, we just assign a base score
            score = 10.0
            if (
                donation["item_type"] == "produce"
                and "produce" in rec_details["accepted_types"]
            ):
                score += 5.0  # Priority for fresh produce

            potential_matches.append(
                {
                    "recipient_id": rec_id,
                    "name": rec_details["name"],
                    "score": score,
                    "capacity_kg": rec_details["capacity_kg"],
                }
            )

        if not potential_matches:
            return {"error": "No suitable recipient found for this donation."}

        # Sort by score descending
        best_match = max(potential_matches, key=lambda x: x["score"])

        # Update donation status
        donation["status"] = "matched"
        donation["matched_recipient"] = best_match["recipient_id"]

        return {
            "donation_id": donation_id,
            "matched_recipient_id": best_match["recipient_id"],
            "recipient_name": best_match["name"],
            "weight_kg": donation["weight_kg"],
        }

    def get_pending_donations(self) -> List[Dict[str, Any]]:
        """Returns all donations that have not yet been matched."""
        return [d for d in self.active_donations if d["status"] == "pending"]
