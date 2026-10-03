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

# 1. Whitelist .gguf in ComfyUI native folder_paths
if hasattr(folder_paths, "supported_pt_extensions"):
    folder_paths.supported_pt_extensions.add(".gguf")

folder_map = getattr(folder_paths, "folder_names_and_paths", {})
for cat, (dirs, exts) in folder_map.items():
    if isinstance(exts, set) and (".safetensors" in exts or ".ckpt" in exts):
        exts.add(".gguf")

# 2. Hook folder_paths.get_filename_list to return up-to-date models without ComfyUI restart
_orig_get_filename_list = folder_paths.get_filename_list

def smart_get_filename_list(folder_name: str) -> list[str]:
    folder_name = folder_paths.map_legacy(folder_name) if hasattr(folder_paths, "map_legacy") else folder_name
    try:
        base_list = set(_orig_get_filename_list(folder_name))
    except Exception:
        base_list = set()

    indexer = SmartModelIndex.get_instance()
    cached_for_cat = indexer.cached_files_by_category.get(folder_name, [])
    for rel_p in cached_for_cat:
        aligned_p = rel_p.replace("/", "\\") if os.sep == "\\" else rel_p
        base_list.add(aligned_p)

    return sorted(list(base_list))

folder_paths.get_filename_list = smart_get_filename_list

# 3. Hook folder_paths.get_full_path
_orig_get_full_path = folder_paths.get_full_path

def smart_get_full_path(folder_name: str, filename: str):
    if not filename or not isinstance(filename, str):
        return _orig_get_full_path(folder_name, filename)

    # 1. Absolute path check
    if os.path.isabs(filename) and (os.path.isfile(filename) or os.path.islink(filename)):
        return filename

    # 2. Standard resolution
    path = _orig_get_full_path(folder_name, filename)
    if path and (os.path.isfile(path) or os.path.islink(path)):
        return path

    # Standard resolution with alternative slash format
    alt_fn = filename.replace("/", "\\") if "/" in filename else filename.replace("\\", "/")
    path_alt = _orig_get_full_path(folder_name, alt_fn)
    if path_alt and (os.path.isfile(path_alt) or os.path.islink(path_alt)):
        return path_alt

    ext = os.path.splitext(filename)[-1].lower()
    if ext and ext not in VALID_MODEL_EXTENSIONS:
        return None

    # 3. SmartModelIndex subfolder / cross-category resolution
    indexer = SmartModelIndex.get_instance()
    res = indexer.find_model(folder_name, filename, folder_paths)
    if res:
        full_p, rel_p, match_type = res
        logger.info(f"[SmartModelResolver] Auto-located exact model: '{filename}' in '{folder_name}' -> '{full_p}' ({match_type})")
        return full_p

    # 4. Fallback search across all category directories
    clean_fn = filename.replace("/", os.sep).replace("\\", os.sep).lstrip(os.sep)
    for cat, (dirs, _) in folder_map.items():
        for d in dirs:
            cand_p = os.path.join(d, clean_fn)
            if os.path.isfile(cand_p) or os.path.islink(cand_p):
                return cand_p

    return None

folder_paths.get_full_path = smart_get_full_path

# Hook execution.validate_prompt & validate_inputs to eliminate value_not_in_list for physical files
try:
    import execution
    import nodes

    _orig_validate_prompt = execution.validate_prompt
    _orig_validate_inputs = getattr(execution, "validate_inputs", None)

    async def smart_validate_prompt(prompt_id, prompt, partial_execution_list=None):
        if prompt and isinstance(prompt, dict):
            indexer = SmartModelIndex.get_instance()
            for node_id, node_data in prompt.items():
                if not isinstance(node_data, dict):
                    continue
                inputs = node_data.get("inputs")
                class_type = node_data.get("class_type")
                if not isinstance(inputs, dict) or not class_type:
                    continue
                class_def = nodes.NODE_CLASS_MAPPINGS.get(class_type)
                if not class_def:
                    continue
                try:
                    class_inputs = class_def.INPUT_TYPES()
                except Exception:
                    continue
                valid_inputs = set(class_inputs.get("required", {})).union(set(class_inputs.get("optional", {})))
                for input_name in valid_inputs:
                    if input_name not in inputs:
                        continue
                    val = inputs[input_name]
                    if not isinstance(val, str):
                        continue
                    ext = os.path.splitext(val)[-1].lower()
                    if ext and ext not in VALID_MODEL_EXTENSIONS:
                        continue

                    info = class_inputs.get("required", {}).get(input_name) or class_inputs.get("optional", {}).get(input_name)
                    if not info:
                        continue
                    combo_options = None
                    if isinstance(info, tuple) and len(info) > 0 and isinstance(info[0], list):
                        combo_options = info[0]
                    elif isinstance(info, tuple) and len(info) > 1 and isinstance(info[1], dict) and "options" in info[1]:
                        combo_options = info[1]["options"]
                    elif isinstance(info, list):
                        combo_options = info

                    if combo_options is None:
                        continue

                    if val in combo_options:
                        continue

                    # 1. Slash-normalized match (e.g. '/' vs '\')
                    norm_val = val.replace("/", "\\").lower()
                    matched = False
                    for opt in combo_options:
                        if not isinstance(opt, str):
                            continue
                        if opt.replace("/", "\\").lower() == norm_val:
                            inputs[input_name] = opt
                            logger.info(f"[SmartModelResolver] Auto-aligned combo input '{input_name}' for node {node_id}: '{val}' -> '{opt}'")
                            matched = True
                            break

                    # 2. Subfolder auto-location if basename matches
                    if not matched:
                        req_base = os.path.basename(val.replace("/", "\\")).lower()
                        for opt in combo_options:
                            if not isinstance(opt, str):
                                continue
                            if os.path.basename(opt.replace("/", "\\")).lower() == req_base:
                                inputs[input_name] = opt
                                logger.info(f"[SmartModelResolver] Auto-located subfolder combo input '{input_name}' for node {node_id}: '{val}' -> '{opt}'")
                                matched = True
                                break

                    # 3. Model physically exists on disk or found via SmartModelIndex
                    if not matched:
                        res = indexer.find_model("", val, folder_paths)
                        if res:
                            full_p, rel_p, match_type = res
                            aligned_p = rel_p.replace("/", "\\") if os.sep == "\\" else rel_p
                            inputs[input_name] = aligned_p
                            if isinstance(combo_options, list):
                                if aligned_p not in combo_options:
                                    combo_options.append(aligned_p)
                                if val not in combo_options:
                                    combo_options.append(val)
                            logger.info(f"[SmartModelResolver] Auto-resolved physical disk model '{input_name}' for node {node_id}: '{val}' -> '{aligned_p}'")

        return await _orig_validate_prompt(prompt_id, prompt, partial_execution_list)

    execution.validate_prompt = smart_validate_prompt

    if _orig_validate_inputs is not None:
        async def smart_validate_inputs(prompt_id, prompt, item, validated, visiting=None):
            res = await _orig_validate_inputs(prompt_id, prompt, item, validated, visiting)
            # res is tuple: (valid: bool, reasons: list, item: str)
            if not res[0] and isinstance(res[1], list):
                new_reasons = []
                for reason in res[1]:
                    if isinstance(reason, dict) and reason.get("type") == "value_not_in_list":
                        extra = reason.get("extra_info", {})
                        inp_name = extra.get("input_name")
                        rec_val = extra.get("received_value")
                        if isinstance(rec_val, str):
                            ext = os.path.splitext(rec_val)[-1].lower()
                            if ext in VALID_MODEL_EXTENSIONS or not ext:
                                # Check if file physically exists on disk anywhere
                                if (os.path.isabs(rec_val) and os.path.isfile(rec_val)) or \
                                   smart_get_full_path("", rec_val) is not None or \
                                   check_file_exists_any_category(folder_paths, rec_val) or \
                                   SmartModelIndex.get_instance().find_model("", rec_val, folder_paths) is not None:
                                    logger.info(f"[SmartModelResolver] Auto-bypassing value_not_in_list for physically verified file: '{rec_val}' (node #{item}, input '{inp_name}')")
                                    continue
                    new_reasons.append(reason)

                if len(new_reasons) == 0:
                    validated[item] = (True, [], item)
                    return (True, [], item)
                elif len(new_reasons) < len(res[1]):
                    validated[item] = (False, new_reasons, item)
                    return (False, new_reasons, item)

            return res

        execution.validate_inputs = smart_validate_inputs
except Exception as e:
    logger.debug(f"[SmartModelResolver] Could not hook execution functions: {e}")

# Pre-index in background daemon thread on startup so ComfyUI starts instantly
def _warmup_indexer():
    try:
        SmartModelIndex.get_instance().scan_all(folder_paths)
    except Exception as e:
        logger.debug(f"[SmartModelResolver] Warmup scan info: {e}")

threading.Thread(target=_warmup_indexer, daemon=True).start()

def check_file_physically_exists(folder_paths, cat: str, filename: str) -> bool:
    if not filename:
        return False
    cat = folder_paths.map_legacy(cat) if hasattr(folder_paths, "map_legacy") else cat
    folder_map = getattr(folder_paths, "folder_names_and_paths", {})
    if cat not in folder_map:
        return False
    dirs, _ = folder_map[cat]
    clean_fn = filename.replace("/", os.sep).replace("\\", os.sep).lstrip(os.sep)
    for d in dirs:
        full_p = os.path.join(d, clean_fn)
        if os.path.isfile(full_p) or os.path.islink(full_p):
            return True
    return False

def check_file_exists_any_category(folder_paths, filename: str) -> bool:
    if not filename:
        return False
    if os.path.isabs(filename) and (os.path.isfile(filename) or os.path.islink(filename)):
        return True
    folder_map = getattr(folder_paths, "folder_names_and_paths", {})
    for cat in folder_map.keys():
        if check_file_physically_exists(folder_paths, cat, filename):
            return True
    indexer = SmartModelIndex.get_instance()
    req_base = os.path.basename(filename.replace("\\", "/")).lower()
    if req_base in indexer.basename_to_paths:
        return True
    return False

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

            # Check if it's already in the widget's available options
            if any(opt.replace("\\", "/").lower() == clean_val_lower for opt in available_vals):
                already_exists = True

            # Check via in-memory indexer (exact relative path)
            if not already_exists:
                disk_matches = indexer.basename_to_paths.get(req_base, [])
                for cat, rel_p in disk_matches:
                    if rel_p.lower() == clean_val_lower:
                        already_exists = True
                        break

            # Check via physical disk check across categories
            if not already_exists and check_file_exists_any_category(folder_paths, current_val):
                already_exists = True

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
            disk_matches = indexer.basename_to_paths.get(req_base, [])
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
                # If matched_val exists in available_vals with different slash formatting, use the exact option string
                norm_matched = matched_val.replace("\\", "/").lower()
                for opt in available_vals:
                    if opt.replace("\\", "/").lower() == norm_matched:
                        matched_val = opt
                        break

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
            # Search for semantic SIMILAR model suggestions!
            # -------------------------------------------------------------
            from .core.model_indexer import calculate_model_similarity

            candidates_map = {}  # opt_path -> score

            # 2a. Check available options in widget (preferred source)
            if available_vals:
                for opt in available_vals:
                    opt_norm = opt.replace("\\", "/")
                    opt_base = os.path.basename(opt_norm).lower()
                    opt_s, opt_e = os.path.splitext(opt_base)
                    if opt_e not in VALID_MODEL_EXTENSIONS or opt_base == req_base:
                        continue
                    score = calculate_model_similarity(req_base, opt_base)
                    if score >= 0.58:
                        candidates_map[opt] = max(candidates_map.get(opt, 0.0), score)
            else:
                # 2b. Fallback to indexing category on disk when available_vals is empty
                sim_list = indexer.find_similar_models(cat_hint, current_val, folder_paths, top_k=3)
                for full_p, rel_p, score in sim_list:
                    candidates_map[rel_p] = max(candidates_map.get(rel_p, 0.0), score)

            if candidates_map:
                sorted_cands = sorted(candidates_map.items(), key=lambda x: x[1], reverse=True)
                # Filter out anything that matches current_val
                valid_cands = [
                    (opt, sc) for opt, sc in sorted_cands
                    if opt.replace("\\", "/").lower() != clean_val_lower
                ]
                if valid_cands:
                    best_cand, best_score = valid_cands[0]
                    alt_list = [{"model": opt, "score": round(sc * 100)} for opt, sc in valid_cands]
                    suggestions.append({
                        "nodeId": node_id,
                        "nodeTitle": node_title,
                        "widgetName": widget_name,
                        "requestedModel": current_val,
                        "suggestedModel": best_cand,
                        "similarityScore": round(best_score * 100),
                        "alternatives": alt_list
                    })

        return web.json_response({
            "resolved": exact_resolved,
            "suggestions": suggestions
        })
    except Exception as e:
        logger.error(f"[SmartModelResolver] API error: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)

async def _handle_refresh_cache_impl(request):
    try:
        # 1. Clear ComfyUI internal caches
        if hasattr(folder_paths, "filename_list_cache"):
            folder_paths.filename_list_cache.clear()
        if hasattr(folder_paths, "cache_helper") and folder_paths.cache_helper is not None:
            folder_paths.cache_helper.clear()

        # 2. Rescan disk models
        indexer = SmartModelIndex.get_instance()
        indexer.scan_all(folder_paths, force=True)

        total_models = sum(len(v) for v in indexer.cached_files_by_category.values())
        logger.info(f"[SmartModelResolver] Local disk cache refreshed: {total_models} models re-indexed.")

        return web.json_response({
            "success": True,
            "total_models": total_models,
            "categories": len(indexer.cached_files_by_category)
        })
    except Exception as e:
        logger.error(f"[SmartModelResolver] Refresh cache error: {e}", exc_info=True)
        return web.json_response({"success": False, "error": str(e)}, status=500)

if hasattr(PromptServer, "instance") and PromptServer.instance is not None:
    PromptServer.instance.routes.post("/smart_model_resolver/resolve_batch")(_handle_resolve_batch_impl)
    PromptServer.instance.routes.post("/smart_model_resolver/refresh_cache")(_handle_refresh_cache_impl)

logger.info("★ ComfyUI-SmartModelResolver ready (Subfolder Auto-Fix + Interactive Model Suggestions + Live Cache Refresh)")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
