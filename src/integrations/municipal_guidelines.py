class MunicipalDatabaseClient:
    """
    Mock client simulating a localized database lookup for municipal waste rules based on Zip Codes.
    Essential for resolving Edge Cases where material sorting rules vary by city (Issue #1472).
    """

    @staticmethod
    def get_sorting_rule(zip_code: str, base_material: str, has_food_residue: bool) -> str:
        """
        Returns the correct waste bin based on local laws.
        """
        
        # Scenario A: Eco-friendly city (e.g. San Francisco)
        # They have industrial composting facilities that can handle greasy cardboard
        if zip_code == "94103":
            if base_material == "Cardboard" and has_food_residue:
                return "Compost"
                
        # Scenario B: Standard city (e.g. Beverly Hills)
        # Greasy cardboard ruins the recycling batch, must be trashed
        elif zip_code == "90210":
            if base_material == "Cardboard" and has_food_residue:
                return "Trash"

        # Default rules for clean materials
        if base_material == "Cardboard":
            return "Recycle"
            
        return "Trash"

municipal_db = MunicipalDatabaseClient()
