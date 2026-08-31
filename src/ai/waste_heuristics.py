import logging
from .vision_api_mock import vision_analyzer
from src.integrations.municipal_guidelines import municipal_db

logger = logging.getLogger(__name__)

class WasteHeuristicsEngine:
    """
    Middleware pipeline replacing the generic Vision API call.
    Implements Object Detection -> Texture Analysis -> Local Guidelines Lookup.
    Resolves Issue #1472 by properly handling edge cases like greasy pizza boxes.
    """

    CONFIDENCE_THRESHOLD = 0.85

    @staticmethod
    def classify_waste(image_id: str, zip_code: str) -> dict:
        """
        Processes the image through the multi-stage heuristics pipeline.
        """
        # 1. Object Detection & Texture Analysis
        vision_data = vision_analyzer.analyze_image(image_id)
        
        base_material = vision_data['base_material']
        texture_data = vision_data['texture']

        # 2. Confidence Check & Fallback Trigger
        if texture_data['texture_confidence'] < WasteHeuristicsEngine.CONFIDENCE_THRESHOLD:
            logger.info(f"Low texture confidence ({texture_data['texture_confidence']}) for {base_material}. Triggering Fallback UI.")
            
            # Short-circuit the classification and ask the user for help
            return {
                "status": "REQUIRES_CLARIFICATION",
                "prompts": [
                    {
                        "question": f"Is there food residue (like grease or cheese) on this {base_material}?",
                        "type": "boolean",
                        "key": "has_food_residue"
                    }
                ]
            }

        # 3. Local Municipal Guidelines Lookup
        # We now have high confidence in both material and texture, so we check local laws.
        final_bin = municipal_db.get_sorting_rule(
            zip_code=zip_code, 
            base_material=base_material, 
            has_food_residue=texture_data['has_food_residue']
        )

        logger.info(f"Classified {image_id} as {final_bin} for zip {zip_code}.")
        
        return {
            "status": "SUCCESS",
            "classification": final_bin,
            "metadata": {
                "material": base_material,
                "had_food_residue": texture_data['has_food_residue']
            }
        }

waste_heuristics_engine = WasteHeuristicsEngine()
