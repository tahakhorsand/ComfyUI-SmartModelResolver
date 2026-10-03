import os
import logging
from aiohttp import web
from server import PromptServer
import folder_paths

from .core.model_indexer import SmartModelIndex, VALID_MODEL_EXTENSIONS
from .nodes.smart_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

logger = logging.getLogger("SmartModelResolver")
WEB_DIRECTORY = "./web"

# Hook folder_paths.get_full_path
_orig_get_full_path = folder_paths.get_full_path

def smart_get_full_path(folder_name: str, filename: str):
    path = _orig_get_full_path(folder_name, filename)
    if path and (os.path.isfile(path) or os.path.islink(path)):
        return path

    indexer = SmartModelIndex.get_instance()
    res = indexer.find_model(folder_name, filename, folder_paths)
    if res:
        full_p, rel_p, match_type = res
        logger.info(f"[SmartModelResolver] Auto-located exact model in subfolder: '{filename}' in '{folder_name}' -> '{full_p}' ({match_type})")
        return full_p

    return None

folder_paths.get_full_path = smart_get_full_path

# Register HTTP endpoint for Frontend Auto-Fixer & Suggestions
async def _handle_resolve_batch_impl(request):
    try:
        data = await request.json()
        entries = data.get("entries", [])
        indexer = SmartModelIndex.get_instance()
        exact_resolved = []
        suggestions = []

        for entry in entries:
            node_id = entry.get("nodeId")
            node_title = entry.get("nodeTitle", "")
            widget_name = entry.get("widgetName", "")
            current_val = entry.get("currentValue", "")
            available_vals = entry.get("availableValues", [])

            if not current_val or not isinstance(current_val, str):
                continue

            clean_val = current_val.strip().replace("\\", "/")
            req_base = os.path.basename(clean_val).lower()
            req_ext = os.path.splitext(req_base)[-1].lower()

            # Strictly ignore non-model files (e.g. .py, .json)
            if req_ext and req_ext not in VALID_MODEL_EXTENSIONS:
                continue

            w_lower = widget_name.lower()
            if "lora" in w_lower:
                cat_hint = "loras"
            elif "unet" in w_lower or "diffusion" in w_lower:
                cat_hint = "diffusion_models"
            elif "vae" in w_lower:
                cat_hint = "vae"
            elif "clip" in w_lower or "text_encoder" in w_lower or "conditioning" in w_lower:
                cat_hint = "text_encoders"
            elif "controlnet" in w_lower:
                cat_hint = "controlnet"
            else:
                cat_hint = "checkpoints"

            matched_val = None
            match_type = ""

            # 1. Check available combo values for EXACT basename match (subfolder path resolution)
            for opt in available_vals:
                opt_norm = opt.replace("\\", "/")
                opt_base = os.path.basename(opt_norm).lower()
                if opt_base == req_base:
                    matched_val = opt
                    match_type = "exact_subfolder_match"
                    break

            # 2. If not found in available_vals, check disk indexer for EXACT same model
            if not matched_val:
                find_res = indexer.find_model(cat_hint, current_val, folder_paths)
                if find_res:
                    full_p, rel_p, match_type = find_res
                    rel_base = os.path.basename(rel_p).lower()
                    for opt in available_vals:
                        if os.path.basename(opt.replace("\\", "/")).lower() == rel_base:
                            matched_val = opt
                            break
                    if not matched_val:
                        matched_val = rel_p

            if matched_val and matched_val != current_val:
                exact_resolved.append({
                    "nodeId": node_id,
                    "widgetName": widget_name,
                    "resolvedValue": matched_val,
                    "matchType": match_type
                })
            elif not matched_val:
                # 3. Model is NOT found on disk. Look for an authentic SIMILAR model to suggest to user!
                sim_res = indexer.find_similar_model(cat_hint, current_val, folder_paths)
                if sim_res:
                    full_p, rel_p, score = sim_res
                    # Find matching representation in available_vals if available
                    cand_base = os.path.basename(rel_p).lower()
                    final_cand = rel_p
                    for opt in available_vals:
                        if os.path.basename(opt.replace("\\", "/")).lower() == cand_base:
                            final_cand = opt
                            break

                    suggestions.append({
                        "nodeId": node_id,
                        "nodeTitle": node_title,
                        "widgetName": widget_name,
                        "requestedModel": current_val,
                        "suggestedModel": final_cand,
                        "similarityScore": round(score * 100)
                    })

        return web.json_response({
            "resolved": exact_resolved,
            "suggestions": suggestions
        })
    except Exception as e:
        logger.error(f"[SmartModelResolver] API error: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)

if hasattr(PromptServer, "instance") and PromptServer.instance is not None:
    PromptServer.instance.routes.post("/smart_model_resolver/resolve_batch")(_handle_resolve_batch_impl)

logger.info("★ ComfyUI-SmartModelResolver ready (Subfolder Auto-Fix + Interactive Model Suggestions)")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
