from .eco_ledger import eco_ledger_db

class PointEngine:
    """
    Deterministic Calculation Engine.
    Instead of trusting a mutable 'points' column in a users table, this engine calculates
    the absolute source of truth by deriving the total score from the user's immutable event ledger.
    """

    @staticmethod
    def calculate_total_points(user_id: str) -> int:
        """
        Calculates the user's total gamification score by summing all ledger events.
        """
        events = eco_ledger_db.get_events_for_user(user_id)
        
        # In a real production system, this could be materialized via a SQL SUM() query
        # e.g., SELECT SUM(points) FROM eco_ledger WHERE user_id = ?
        
        total = sum(event['points'] for event in events)
        return total
