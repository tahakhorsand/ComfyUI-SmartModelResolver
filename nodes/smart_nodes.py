import os
import folder_paths
from ..core.model_indexer import SmartModelIndex

try:
    from comfy_api.latest import ComfyExtension, io, ui
    HAS_COMFY_V3 = True
except ImportError:
    HAS_COMFY_V3 = False
    # Fallback dummy base class for legacy ComfyUI environments
    class io:
        class ComfyNode:
            pass


class SmartModelPathFinder(io.ComfyNode if HAS_COMFY_V3 else object):
    """
    Dedicated utility node to dynamically locate model files across all subfolders
    and categories in ComfyUI models directory.
    Supports both ComfyUI V3 (Nodes 2.0 API) and legacy V1 architecture.
    """

    # -------------------------------------------------------------------------
    # V3 (Nodes 2.0) Schema Definition
    # -------------------------------------------------------------------------
    @classmethod
    def define_schema(cls):
        if not HAS_COMFY_V3:
            return None

        categories = ["ALL"] + sorted(list(getattr(folder_paths, "folder_names_and_paths", {}).keys()))
        return io.Schema(
            node_id="SmartModelPathFinder",
            display_name="Smart Model Path Finder (Deep Subfolder Locator)",
            category="SmartModelResolver",
            description="Dynamically locates model files across all subfolders and categories in ComfyUI.",
            inputs=[
                io.String.Input("model_name", default="marigold_v2_normals.safetensors", multiline=False, tooltip="Model filename to find (e.g. model.safetensors or folder/model.safetensors)"),
                io.Combo.Input("category", options=categories, default="ALL", tooltip="Target model category directory or 'ALL' to search across categories"),
                io.Boolean.Input("allow_fuzzy", default=True, tooltip="Allow fuzzy semantic matching if exact filename is not found"),
            ],
            outputs=[
                io.String.Output(display_name="full_path"),
                io.String.Output(display_name="relative_path"),
                io.Boolean.Output(display_name="found"),
                io.String.Output(display_name="match_info"),
            ],
        )

    # -------------------------------------------------------------------------
    # V3 Execution Method
    # -------------------------------------------------------------------------
    @classmethod
    def execute(cls, model_name: str, category: str, allow_fuzzy: bool = True):
        indexer = SmartModelIndex.get_instance()
        target_cat = "checkpoints" if category == "ALL" else category

        # 1. Exact subfolder / cross-category resolution
        res = indexer.find_model(target_cat, model_name, folder_paths)
        if res:
            full_p, rel_p, match_type = res
            if HAS_COMFY_V3:
                return io.NodeOutput(full_p, rel_p, True, f"Found via {match_type}")
            return (full_p, rel_p, True, f"Found via {match_type}")

        # If ALL was selected and not found, try searching across common model categories
        if category == "ALL":
            for cat in ["diffusion_models", "loras", "vae", "text_encoders", "checkpoints", "controlnet", "upscale_models"]:
                res = indexer.find_model(cat, model_name, folder_paths)
                if res:
                    full_p, rel_p, match_type = res
                    if HAS_COMFY_V3:
                        return io.NodeOutput(full_p, rel_p, True, f"Found in {cat} via {match_type}")
                    return (full_p, rel_p, True, f"Found in {cat} via {match_type}")

        # 2. Fuzzy similarity search if allowed
        if allow_fuzzy:
            search_cat = "diffusion_models" if category == "ALL" else category
            sim_list = indexer.find_similar_models(search_cat, model_name, folder_paths, top_k=1)
            if sim_list:
                full_p, rel_p, score = sim_list[0]
                if score >= 0.55:
                    msg = f"Found similar candidate ({int(score * 100)}% match): {rel_p}"
                    if HAS_COMFY_V3:
                        return io.NodeOutput(full_p, rel_p, True, msg)
                    return (full_p, rel_p, True, msg)

        not_found_msg = f"Model '{model_name}' not found anywhere in models/ directory."
        if HAS_COMFY_V3:
            return io.NodeOutput("", "", False, not_found_msg)
        return ("", "", False, not_found_msg)

    # -------------------------------------------------------------------------
    # V1 (Legacy) Interface Definition
    # -------------------------------------------------------------------------
    @classmethod
    def INPUT_TYPES(cls):
        categories = ["ALL"] + sorted(list(getattr(folder_paths, "folder_names_and_paths", {}).keys()))
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
        res = self.execute(model_name, category, allow_fuzzy)
        if hasattr(res, "__getitem__"):
            return (res[0], res[1], res[2], res[3])
        return ("", "", False, "Execution error")


# V3 Extension definition
if HAS_COMFY_V3:
    class SmartModelResolverExtension(ComfyExtension):
        async def get_node_list(self) -> list[type[io.ComfyNode]]:
            return [SmartModelPathFinder]

    async def comfy_entrypoint() -> SmartModelResolverExtension:
        return SmartModelResolverExtension()
else:
    async def comfy_entrypoint():
        return None


# V1 Mapping definitions
NODE_CLASS_MAPPINGS = {
    "SmartModelPathFinder": SmartModelPathFinder
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SmartModelPathFinder": "🔍 Smart Model Path Finder (Deep Subfolder Locator)"
}
