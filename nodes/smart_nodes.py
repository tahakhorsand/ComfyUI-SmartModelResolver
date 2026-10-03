import os
import folder_paths
from ..core.model_indexer import SmartModelIndex

class SmartModelPathFinder:
    """
    Dedicated utility node to dynamically locate model files across all subfolders
    and categories in ComfyUI models directory.
    """
    @classmethod
    def INPUT_TYPES(s):
        categories = ["ALL"] + sorted(list(folder_paths.folder_names_and_paths.keys()))
        return {
            "required": {
                "model_name": ("STRING", {"default": "marigold_v2_normals.safetensors", "multiline": False}),
                "category": (categories, {"default": "ALL"}),
                "allow_fuzzy": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = ("full_path", "relative_path", "found", "match_info")
    FUNCTION = "resolve"
    CATEGORY = "SmartModelResolver"

    def resolve(self, model_name: str, category: str, allow_fuzzy: bool = True):
        indexer = SmartModelIndex.get_instance()
        target_cat = "checkpoints" if category == "ALL" else category
        
        res = indexer.find_model(target_cat, model_name, folder_paths, allow_fuzzy=allow_fuzzy)
        if res:
            full_p, rel_p, match_type = res
            return (full_p, rel_p, True, f"Found via {match_type}")
        
        # If ALL was selected and not found, try searching across common categories
        if category == "ALL":
            for cat in ["loras", "diffusion_models", "vae", "text_encoders", "controlnet"]:
                res = indexer.find_model(cat, model_name, folder_paths, allow_fuzzy=allow_fuzzy)
                if res:
                    full_p, rel_p, match_type = res
                    return (full_p, rel_p, True, f"Found in {cat} via {match_type}")

        return ("", "", False, f"Model '{model_name}' not found anywhere in models/ directory.")

NODE_CLASS_MAPPINGS = {
    "SmartModelPathFinder": SmartModelPathFinder
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SmartModelPathFinder": "🔍 Smart Model Path Finder (Deep Subfolder Locator)"
}
