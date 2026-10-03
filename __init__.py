import os
import re
import difflib
import threading
import logging
from aiohttp import web
from server import PromptServer
import folder_paths

from .core.model_indexer import SmartModelIndex, VALID_MODEL_EXTENSIONS, GENERIC_SUFFIX_TOKENS
from .nodes.smart_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

logger = logging.getLogger("SmartModelResolver")
WEB_DIRECTORY = "./web"

# Hook folder_paths.get_full_path
_orig_get_full_path = folder_paths.get_full_path

def smart_get_full_path(folder_name: str, filename: str):
    if not filename or not isinstance(filename, str):
        return _orig_get_full_path(folder_name, filename)

    path = _orig_get_full_path(folder_name, filename)
    if path and (os.path.isfile(path) or os.path.islink(path)):
        return path

    ext = os.path.splitext(filename)[-1].lower()
    if ext and ext not in VALID_MODEL_EXTENSIONS:
        return None

    indexer = SmartModelIndex.get_instance()
    res = indexer.find_model(folder_name, filename, folder_paths)
    if res:
        full_p, rel_p, match_type = res
        logger.info(f"[SmartModelResolver] Auto-located exact model in subfolder: '{filename}' in '{folder_name}' -> '{full_p}' ({match_type})")
        return full_p

    return None

folder_paths.get_full_path = smart_get_full_path

# Pre-index in background daemon thread on startup so ComfyUI starts instantly
def _warmup_indexer():
    try:
        SmartModelIndex.get_instance().scan_all(folder_paths)
    except Exception as e:
        logger.debug(f"[SmartModelResolver] Warmup scan info: {e}")

threading.Thread(target=_warmup_indexer, daemon=True).start()

# Register HTTP endpoint for Frontend Auto-Fixer & Suggestions
async def _handle_resolve_batch_impl(request):
    try:
        data = await request.json()
        entries = data.get("entries", [])
        indexer = SmartModelIndex.get_instance()
        indexer.scan_all(folder_paths)
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
            clean_val_lower = clean_val.lower()
            req_base = os.path.basename(clean_val).lower()
            req_stem, req_ext = os.path.splitext(req_base)

            # Strictly ignore non-model files (e.g. .py, .json)
            if req_ext and req_ext not in VALID_MODEL_EXTENSIONS:
                continue

            # -------------------------------------------------------------
            # STEP 0: Check if this model ALREADY exists physically on disk!
            # If current_val is already at the requested path, it is NOT missing!
            # -------------------------------------------------------------
            already_exists = False
            disk_matches = indexer.basename_to_paths.get(req_base, [])

            # Check via in-memory index
            for cat, rel_p in disk_matches:
                if rel_p.lower() == clean_val_lower:
                    already_exists = True
                    break

            # Check via folder_paths across all categories
            if not already_exists:
                for cat in list(getattr(folder_paths, "folder_names_and_paths", {}).keys()):
                    try:
                        p = folder_paths.get_full_path(cat, current_val)
                        if p and (os.path.isfile(p) or os.path.islink(p)):
                            already_exists = True
                            break
                    except Exception:
                        pass

            if already_exists:
                # Model is present on disk at this exact relative path.
                # DO NOT TOUCH IT! DO NOT SUGGEST REPLACING IT!
                continue

            # Contextual category detection from both widget name and node title
            context = f"{widget_name} {node_title}".lower()
            if "lora" in context:
                cat_hint = "loras"
            elif "unet" in context or "diffusion" in context:
                cat_hint = "diffusion_models"
            elif "vae" in context:
                cat_hint = "vae"
            elif any(k in context for k in ["clip", "text_encoder", "conditioning", "t5", "gemma", "prompt", "enhance", "llm"]):
                cat_hint = "text_encoders"
            elif "controlnet" in context:
                cat_hint = "controlnet"
            elif "upscale" in context:
                cat_hint = "upscale_models"
            else:
                cat_hint = "checkpoints"

            target_cat = folder_paths.map_legacy(cat_hint) if hasattr(folder_paths, "map_legacy") else cat_hint

            # -------------------------------------------------------------
            # STEP 1: Exact model exists on disk, but in a SUBFOLDER!
            # (e.g. requested 'marigold_v2.safetensors', but stored in 'marigold/marigold_v2.safetensors')
            # -------------------------------------------------------------
            matched_val = None
            match_type = ""

            # Check available_vals for exact basename match (subfolder path)
            for opt in available_vals:
                opt_norm = opt.replace("\\", "/")
                opt_base = os.path.basename(opt_norm).lower()
                if opt_base == req_base:
                    if opt_norm.lower() != clean_val_lower:
                        matched_val = opt
                        match_type = "exact_subfolder_match"
                        break

            # If not in available_vals, check disk indexer
            if not matched_val and disk_matches:
                # Prioritize matching category
                for cat, rel_p in disk_matches:
                    if cat == target_cat and rel_p.lower() != clean_val_lower:
                        matched_val = rel_p
                        match_type = "exact_category_subfolder"
                        break
                if not matched_val:
                    for cat, rel_p in disk_matches:
                        if rel_p.lower() != clean_val_lower:
                            matched_val = rel_p
                            match_type = f"cross_category_{cat}"
                            break

            if matched_val:
                # Only add if it's genuinely a different relative path (ignoring case & slashes)
                if matched_val.replace("\\", "/").lower() != clean_val_lower:
                    exact_resolved.append({
                        "nodeId": node_id,
                        "nodeTitle": node_title,
                        "widgetName": widget_name,
                        "originalValue": current_val,
                        "resolvedValue": matched_val,
                        "matchType": match_type
                    })
                continue

            # -------------------------------------------------------------
            # STEP 2: Model file truly DOES NOT EXIST anywhere on the system!
            # Only in this case can we search for SIMILAR model suggestions!
            # -------------------------------------------------------------
            best_sim_cand = None
            best_sim_score = 0.0

            clean_req_tokens = set(re.findall(r'[a-zA-Z0-9]+', req_stem))
            req_identity = clean_req_tokens - GENERIC_SUFFIX_TOKENS

            # Prioritize available options for this exact widget first
            for opt in available_vals:
                opt_norm = opt.replace("\\", "/")
                opt_base = os.path.basename(opt_norm).lower()
                opt_s, opt_e = os.path.splitext(opt_base)
                if opt_e not in VALID_MODEL_EXTENSIONS or opt_base == req_base:
                    continue
                opt_tokens = set(re.findall(r'[a-zA-Z0-9]+', opt_s))
                opt_identity = opt_tokens - GENERIC_SUFFIX_TOKENS
                common_identity = req_identity.intersection(opt_identity)
                if not common_identity and not (req_stem[:5] == opt_s[:5] and len(req_stem) > 4):
                    continue
                score = difflib.SequenceMatcher(None, req_stem, opt_s).ratio()
                if score > best_sim_score:
                    best_sim_score = score
                    best_sim_cand = opt

            # Fallback to indexing category on disk
            if not best_sim_cand or best_sim_score < 0.58:
                sim_res = indexer.find_similar_model(cat_hint, current_val, folder_paths)
                if sim_res:
                    full_p, rel_p, score = sim_res
                    if score > best_sim_score:
                        best_sim_score = score
                        cand_base = os.path.basename(rel_p).lower()
                        best_sim_cand = rel_p
                        for opt in available_vals:
                            if os.path.basename(opt.replace("\\", "/")).lower() == cand_base:
                                best_sim_cand = opt
                                break

            if best_sim_cand and best_sim_score >= 0.58:
                # Ensure the suggested model is NOT identical to current_val
                if best_sim_cand.replace("\\", "/").lower() != clean_val_lower:
                    suggestions.append({
                        "nodeId": node_id,
                        "nodeTitle": node_title,
                        "widgetName": widget_name,
                        "requestedModel": current_val,
                        "suggestedModel": best_sim_cand,
                        "similarityScore": round(best_sim_score * 100)
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
