class SimulatedVisionAnalyzer:
    """
    Mocks a 3rd-party computer vision API (like Google Cloud Vision or AWS Rekognition).
    In a real implementation, this would process the image bytes. Here we simulate
    extracting both the base material and specific texture anomalies.
    """

    @staticmethod
    def analyze_image(image_id: str) -> dict:
        """
        Simulates an API response based on the mocked image_id.
        """
        # Mocking a greasy pizza box scenario
        if image_id == "pizza_box_greasy":
            return {
                "base_material": "Cardboard",
                "material_confidence": 0.98,
                "texture": {
                    "has_food_residue": True,
                    "residue_type": "Grease",
                    "texture_confidence": 0.92
                }
            }
            
        # Mocking a pizza box where the glare/angle makes the texture uncertain
        elif image_id == "pizza_box_uncertain":
            return {
                "base_material": "Cardboard",
                "material_confidence": 0.95,
                "texture": {
                    "has_food_residue": None,
                    "residue_type": None,
                    "texture_confidence": 0.65  # Below the 0.85 threshold
                }
            }
            
        # Standard clean cardboard
        return {
            "base_material": "Cardboard",
            "material_confidence": 0.99,
            "texture": {
                "has_food_residue": False,
                "residue_type": None,
                "texture_confidence": 0.95
            }
        }

vision_analyzer = SimulatedVisionAnalyzer()
