import os
import folder_paths
from ..core.model_indexer import SmartModelIndex, NON_MODEL_CATEGORIES

try:
    from comfy_api.latest import ComfyExtension, io, ui
    HAS_COMFY_V3 = True
except ImportError:
    HAS_COMFY_V3 = False


def _get_model_categories() -> list[str]:
    folder_map = getattr(folder_paths, "folder_names_and_paths", {})
    return ["ALL"] + sorted(k for k in folder_map.keys() if k not in NON_MODEL_CATEGORIES)


def _resolve_model_path(model_name: str, category: str, allow_fuzzy: bool = True) -> tuple[str, str, bool, str]:
    """Shared lookup logic across V3 and V1 node implementations."""
    indexer = SmartModelIndex.get_instance()
    is_all = (category == "ALL")
    target_cat = "" if is_all else category

    # 1. Exact subfolder / (when ALL) cross-category resolution
    res = indexer.find_model(target_cat, model_name, folder_paths, allow_cross_category=is_all)
    if res:
        full_p, rel_p, match_type = res
        return (full_p, rel_p, True, f"Found via {match_type}")

    # 2. Fuzzy similarity search if allowed
    if allow_fuzzy:
        search_cat = "ALL" if is_all else category
        sim_list = indexer.find_similar_models(search_cat, model_name, folder_paths, top_k=1)
        if sim_list:
            full_p, rel_p, score = sim_list[0]
            if score >= 0.55:
                msg = f"Found similar candidate ({int(score * 100)}% match): {rel_p}"
                return (full_p, rel_p, True, msg)

    not_found_msg = f"Model '{model_name}' not found anywhere in models/ directory."
    return ("", "", False, not_found_msg)


if HAS_COMFY_V3:
    class SmartModelPathFinder(io.ComfyNode):
        """
        Dedicated V3 (Nodes 2.0) utility node to dynamically locate model files
        across subfolders and compatible categories in ComfyUI's models directory.
        """

        @classmethod
        def define_schema(cls) -> io.Schema:
            return io.Schema(
                node_id="SmartModelPathFinder",
                display_name="🔍 Smart Model Path Finder (Deep Subfolder Locator)",
                category="SmartModelResolver",
                description="Dynamically locates model files across all subfolders and categories in ComfyUI.",
                inputs=[
                    io.String.Input(
                        "model_name",
                        default="marigold_v2_normals.safetensors",
                        multiline=False,
                        tooltip="Model filename to find (e.g. model.safetensors or folder/model.safetensors)",
                    ),
                    io.Combo.Input(
                        "category",
                        options=_get_model_categories(),
                        default="ALL",
                        tooltip="Target model category directory or 'ALL' to search across categories",
                    ),
                    io.Boolean.Input(
                        "allow_fuzzy",
                        default=True,
                        tooltip="Allow fuzzy semantic matching if exact filename is not found",
                    ),
                ],
                outputs=[
                    io.String.Output(display_name="full_path"),
                    io.String.Output(display_name="relative_path"),
                    io.Boolean.Output(display_name="found"),
                    io.String.Output(display_name="match_info"),
                ],
            )

        @classmethod
        def execute(cls, model_name: str, category: str, allow_fuzzy: bool = True) -> io.NodeOutput:
            full_p, rel_p, found, info = _resolve_model_path(model_name, category, allow_fuzzy)
            return io.NodeOutput(full_p, rel_p, found, info)

    class SmartModelResolverExtension(ComfyExtension):
        async def get_node_list(self) -> list[type[io.ComfyNode]]:
            return [SmartModelPathFinder]

    async def comfy_entrypoint() -> SmartModelResolverExtension:
        return SmartModelResolverExtension()
else:
    class SmartModelPathFinder:
        """
        Legacy V1 fallback utility node for ComfyUI versions without comfy_api.latest.
        """

        @classmethod
        def INPUT_TYPES(cls):
            return {
                "required": {
                    "model_name": ("STRING", {"default": "marigold_v2_normals.safetensors", "multiline": False}),
                    "category": (_get_model_categories(), {"default": "ALL"}),
                    "allow_fuzzy": ("BOOLEAN", {"default": True}),
                }
            }

        RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "STRING")
        RETURN_NAMES = ("full_path", "relative_path", "found", "match_info")
        FUNCTION = "resolve"
        CATEGORY = "SmartModelResolver"

        @classmethod
        def execute(cls, model_name: str, category: str, allow_fuzzy: bool = True):
            return _resolve_model_path(model_name, category, allow_fuzzy)

        def resolve(self, model_name: str, category: str, allow_fuzzy: bool = True):
            return _resolve_model_path(model_name, category, allow_fuzzy)

    async def comfy_entrypoint():
        return None

    NODE_CLASS_MAPPINGS = {
        "SmartModelPathFinder": SmartModelPathFinder
    }

    NODE_DISPLAY_NAME_MAPPINGS = {
        "SmartModelPathFinder": "🔍 Smart Model Path Finder (Deep Subfolder Locator)"
    }
