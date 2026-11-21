import os
import re
import asyncio
import difflib
import threading
import logging
from aiohttp import web
from server import PromptServer
import folder_paths

from .core.model_indexer import (
    SmartModelIndex,
    VALID_MODEL_EXTENSIONS,
    GENERIC_SUFFIX_TOKENS,
    NON_MODEL_CATEGORIES,
    get_compatible_categories,
)
from .nodes.smart_nodes import HAS_COMFY_V3, SmartModelPathFinder, comfy_entrypoint

if not HAS_COMFY_V3:
    from .nodes.smart_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

logger = logging.getLogger("SmartModelResolver")
WEB_DIRECTORY = "./web"


def _is_safe_subpath(base_dir: str, cand_path: str) -> bool:
    """Verify cand_path resolves inside base_dir (blocks .. traversal)."""
    try:
        real_base = os.path.realpath(base_dir)
        real_cand = os.path.realpath(cand_path)
        return os.path.commonpath([real_base, real_cand]) == real_base
    except Exception:
        return False


def _has_unsafe_path_parts(filename: str) -> bool:
    """Reject traversal segments ('..') or drive-qualified relative tricks."""
    if not filename or not isinstance(filename, str):
        return True
    parts = re.split(r"[/\\]+", filename.strip())
    return ".." in parts


def _infer_category_hint(widget_name: str, context_title: str = "") -> str:
    """Infer ComfyUI model category folder hint from widget name and node title/type."""
    context = f"{widget_name} {context_title}".lower()
    if "lora" in context:
        return "loras"
    if "unet" in context or "diffusion" in context:
        return "diffusion_models"
    if "vae" in context:
        return "vae"
    if any(k in context for k in ["clip", "text_encoder", "conditioning", "t5", "gemma", "prompt", "enhance", "llm"]):
        return "text_encoders"
    if "controlnet" in context:
        return "controlnet"
    if "upscale" in context:
        return "upscale_models"
    return "checkpoints"


# 1. Whitelist .gguf in ComfyUI native folder_paths
if hasattr(folder_paths, "supported_pt_extensions"):
    folder_paths.supported_pt_extensions.add(".gguf")

folder_map = getattr(folder_paths, "folder_names_and_paths", {})
for cat, (dirs, exts) in folder_map.items():
    if isinstance(exts, set) and (".safetensors" in exts or ".ckpt" in exts):
        exts.add(".gguf")

# 2. Hook folder_paths.get_filename_list to return up-to-date models without ComfyUI restart
_orig_get_filename_list = getattr(folder_paths, "_smr_orig_get_filename_list", folder_paths.get_filename_list)
folder_paths._smr_orig_get_filename_list = _orig_get_filename_list


def smart_get_filename_list(folder_name: str) -> list[str]:
    folder_name = folder_paths.map_legacy(folder_name) if hasattr(folder_paths, "map_legacy") else folder_name
    try:
        base_list = set(_orig_get_filename_list(folder_name))
    except Exception:
        base_list = set()

    if folder_name not in NON_MODEL_CATEGORIES:
        indexer = SmartModelIndex.get_instance()
        cached_for_cat = indexer.cached_files_by_category.get(folder_name, [])
        for rel_p in cached_for_cat:
            aligned_p = rel_p.replace("/", "\\") if os.sep == "\\" else rel_p
            base_list.add(aligned_p)

    return sorted(list(base_list))


folder_paths.get_filename_list = smart_get_filename_list

# 3. Hook folder_paths.get_full_path
_orig_get_full_path = getattr(folder_paths, "_smr_orig_get_full_path", folder_paths.get_full_path)
folder_paths._smr_orig_get_full_path = _orig_get_full_path


def smart_get_full_path(folder_name: str, filename: str):
    if not filename or not isinstance(filename, str):
        return _orig_get_full_path(folder_name, filename)

    ext = os.path.splitext(filename)[-1].lower()

    # 1. Absolute path check (strictly limited to valid model file extensions)
    if os.path.isabs(filename):
        if ext in VALID_MODEL_EXTENSIONS and (os.path.isfile(filename) or os.path.islink(filename)):
            return filename
        return None

    # 2. Standard resolution
    path = _orig_get_full_path(folder_name, filename)
    if path and (os.path.isfile(path) or os.path.islink(path)):
        return path

    # Standard resolution with alternative slash format
    alt_fn = filename.replace("/", "\\") if "/" in filename else filename.replace("\\", "/")
    path_alt = _orig_get_full_path(folder_name, alt_fn)
    if path_alt and (os.path.isfile(path_alt) or os.path.islink(path_alt)):
        return path_alt

    if ext and ext not in VALID_MODEL_EXTENSIONS:
        return None

    # 3. SmartModelIndex subfolder / cross-category resolution
    indexer = SmartModelIndex.get_instance()
    res = indexer.find_model(folder_name, filename, folder_paths)
    if res and isinstance(res, (tuple, list)) and len(res) == 3:
        full_p, rel_p, match_type = res
        logger.info(f"[SmartModelResolver] Auto-located exact model: '{filename}' in '{folder_name}' -> '{full_p}' ({match_type})")
        return full_p

    # 4. Fallback search across compatible category directories (with path traversal guard)
    if _has_unsafe_path_parts(filename):
        return None
    clean_fn = filename.replace("/", os.sep).replace("\\", os.sep).lstrip(os.sep)
    cur_folder_map = getattr(folder_paths, "folder_names_and_paths", {})
    if folder_name and folder_name != "ALL":
        search_cats = get_compatible_categories(folder_name, folder_paths)
    else:
        search_cats = [c for c in cur_folder_map.keys() if c not in NON_MODEL_CATEGORIES]
    for cat in search_cats:
        if cat not in cur_folder_map:
            continue
        dirs, _ = cur_folder_map[cat]
        for d in dirs:
            cand_p = os.path.join(d, clean_fn)
            if _is_safe_subpath(d, cand_p) and (os.path.isfile(cand_p) or os.path.islink(cand_p)):
                return cand_p

    return None


folder_paths.get_full_path = smart_get_full_path

# Hook execution.validate_prompt & validate_inputs to eliminate value_not_in_list for physical files
try:
    import execution
    import nodes

    _orig_validate_prompt = getattr(execution, "_smr_orig_validate_prompt", execution.validate_prompt)
    execution._smr_orig_validate_prompt = _orig_validate_prompt
    _orig_validate_inputs = getattr(execution, "_smr_orig_validate_inputs", getattr(execution, "validate_inputs", None))
    if _orig_validate_inputs is not None:
        execution._smr_orig_validate_inputs = _orig_validate_inputs

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

                    has_model_opts = any(
                        isinstance(opt, str) and os.path.splitext(opt)[-1].lower() in VALID_MODEL_EXTENSIONS
                        for opt in combo_options
                    )
                    if not ext and not has_model_opts:
                        continue

                    if val in combo_options:
                        continue

                    # 1. Slash-normalized match (e.g. '/' vs '\')
                    norm_val = val.replace("\\", "/").lower()
                    matched = False
                    for opt in combo_options:
                        if not isinstance(opt, str):
                            continue
                        if opt.replace("\\", "/").lower() == norm_val:
                            inputs[input_name] = opt
                            logger.info(f"[SmartModelResolver] Auto-aligned combo input '{input_name}' for node {node_id}: '{val}' -> '{opt}'")
                            matched = True
                            break

                    # 2. Subfolder auto-location if basename matches
                    if not matched:
                        req_base = os.path.basename(val.replace("\\", "/")).lower()
                        for opt in combo_options:
                            if not isinstance(opt, str):
                                continue
                            if os.path.basename(opt.replace("\\", "/")).lower() == req_base:
                                inputs[input_name] = opt
                                logger.info(f"[SmartModelResolver] Auto-located subfolder combo input '{input_name}' for node {node_id}: '{val}' -> '{opt}'")
                                matched = True
                                break

                    # 3. Model physically exists on disk or found via SmartModelIndex
                    if not matched:
                        cat_hint = _infer_category_hint(input_name, class_type)
                        res = indexer.find_model(cat_hint, val, folder_paths)
                        if res:
                            full_p, rel_p, match_type = res
                            aligned_p = rel_p.replace("/", "\\") if os.sep == "\\" else rel_p
                            inputs[input_name] = aligned_p
                            logger.info(f"[SmartModelResolver] Auto-resolved physical disk model '{input_name}' for node {node_id}: '{val}' -> '{aligned_p}'")

        return await _orig_validate_prompt(prompt_id, prompt, partial_execution_list)

    execution.validate_prompt = smart_validate_prompt

    if _orig_validate_inputs is not None:
        async def smart_validate_inputs(prompt_id, prompt, item, validated, visiting=None):
            res = await _orig_validate_inputs(prompt_id, prompt, item, validated, visiting)
            # res is tuple: (valid: bool, reasons: list, item: str)
            # Note: Downstream nodes whose upstream failed return (False, [], item) -> do NOT touch empty reasons!
            if not res[0] and isinstance(res[1], list) and len(res[1]) > 0:
                node_class_type = prompt.get(item, {}).get("class_type", "") if isinstance(prompt, dict) else ""
                new_reasons = []
                for reason in res[1]:
                    if isinstance(reason, dict) and reason.get("type") == "value_not_in_list":
                        extra = reason.get("extra_info", {})
                        inp_name = extra.get("input_name")
                        rec_val = extra.get("received_value")
                        if isinstance(rec_val, str):
                            ext = os.path.splitext(rec_val)[-1].lower()
                            if ext in VALID_MODEL_EXTENSIONS:
                                cat_hint = _infer_category_hint(inp_name or "", node_class_type)
                                compat_cats = get_compatible_categories(cat_hint, folder_paths)
                                # Check if file physically exists in compatible categories (or absolute path)
                                if (os.path.isabs(rec_val) and os.path.isfile(rec_val)) or \
                                   smart_get_full_path(cat_hint, rec_val) is not None or \
                                   check_file_exists_any_category(folder_paths, rec_val, categories=compat_cats) or \
                                   SmartModelIndex.get_instance().find_model(cat_hint, rec_val, folder_paths) is not None:
                                    logger.info(f"[SmartModelResolver] Auto-bypassing value_not_in_list for physically verified file: '{rec_val}' (node #{item}, input '{inp_name}')")
                                    continue
                    new_reasons.append(reason)

                if len(new_reasons) == 0:
                    # Preserve failure if any upstream linked node failed validation
                    upstream_failed = False
                    prompt_inputs = prompt.get(item, {}).get("inputs", {}) if isinstance(prompt, dict) else {}
                    if isinstance(prompt_inputs, dict) and isinstance(validated, dict):
                        for inp_v in prompt_inputs.values():
                            if isinstance(inp_v, list) and len(inp_v) == 2:
                                up_key = inp_v[0]
                                up_entry = validated.get(up_key)
                                if up_entry is None and up_key is not None:
                                    up_entry = validated.get(str(up_key))
                                if up_entry is not None and not up_entry[0]:
                                    upstream_failed = True
                                    break
                    if upstream_failed:
                        validated[item] = (False, [], item)
                        return (False, [], item)
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
    if not filename or _has_unsafe_path_parts(filename):
        return False
    cat = folder_paths.map_legacy(cat) if hasattr(folder_paths, "map_legacy") else cat
    folder_map = getattr(folder_paths, "folder_names_and_paths", {})
    if cat not in folder_map:
        return False
    dirs, _ = folder_map[cat]
    clean_fn = filename.replace("/", os.sep).replace("\\", os.sep).lstrip(os.sep)
    for d in dirs:
        full_p = os.path.join(d, clean_fn)
        if _is_safe_subpath(d, full_p) and (os.path.isfile(full_p) or os.path.islink(full_p)):
            return True
    return False


def check_file_exists_any_category(folder_paths, filename: str, categories=None) -> bool:
    if not filename or not isinstance(filename, str):
        return False
    ext = os.path.splitext(filename)[-1].lower()
    if os.path.isabs(filename):
        return ext in VALID_MODEL_EXTENSIONS and (os.path.isfile(filename) or os.path.islink(filename))
    folder_map = getattr(folder_paths, "folder_names_and_paths", {})
    target_cats = categories if categories is not None else [c for c in folder_map.keys() if c not in NON_MODEL_CATEGORIES]
    for cat in target_cats:
        if check_file_physically_exists(folder_paths, cat, filename):
            return True
    return False

# Register HTTP endpoint for Frontend Auto-Fixer & Suggestions
async def _handle_resolve_batch_impl(request):
    try:
        data = await request.json()
        entries = data.get("entries", [])
        indexer = SmartModelIndex.get_instance()
        await asyncio.to_thread(indexer.scan_all, folder_paths)
        exact_resolved = []
        suggestions = []

        for entry in entries:
            node_id = entry.get("nodeId")
            node_key = entry.get("nodeKey", "")
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

            has_model_opts = any(
                isinstance(opt, str) and os.path.splitext(opt)[-1].lower() in VALID_MODEL_EXTENSIONS
                for opt in available_vals
            )
            # Strictly ignore non-model files (.py, .json, etc.) and extensionless non-model strings
            if (not req_ext and not has_model_opts) or (req_ext and req_ext not in VALID_MODEL_EXTENSIONS):
                continue

            # Contextual category detection from both widget name and node title
            cat_hint = _infer_category_hint(widget_name, node_title)
            map_fn = getattr(folder_paths, "map_legacy", None)
            target_cat = map_fn(cat_hint) if callable(map_fn) else cat_hint
            compatible_cats = get_compatible_categories(target_cat, folder_paths)
            compatible_cats_set = set(compatible_cats)

            # -------------------------------------------------------------
            # STEP 0: Check if this model ALREADY exists physically on disk!
            # If current_val is already at the requested path, it is NOT missing!
            # -------------------------------------------------------------
            already_exists = False

            # Check if it's already in the widget's available options
            if any(isinstance(opt, str) and opt.replace("\\", "/").lower() == clean_val_lower for opt in available_vals):
                already_exists = True

            # Check via in-memory indexer (exact relative path within compatible categories)
            if not already_exists:
                disk_matches = indexer.basename_to_paths.get(req_base, [])
                for cat, rel_p in disk_matches:
                    mapped_cat = map_fn(cat) if callable(map_fn) else cat
                    if (cat in compatible_cats_set or mapped_cat in compatible_cats_set) and rel_p.lower() == clean_val_lower:
                        already_exists = True
                        break

            # Check via physical disk check across compatible categories (or absolute path)
            if not already_exists and check_file_exists_any_category(folder_paths, current_val, categories=compatible_cats):
                already_exists = True

            # Standard ComfyUI get_full_path check (exact relative path only, NOT fuzzy subfolder search)
            if not already_exists:
                for c in compatible_cats:
                    p = _orig_get_full_path(c, current_val)
                    if p and (os.path.isfile(p) or os.path.islink(p)):
                        already_exists = True
                        break

            if already_exists:
                # Model is present on disk at this exact relative path.
                # DO NOT TOUCH IT! DO NOT SUGGEST REPLACING IT!
                continue

            # -------------------------------------------------------------
            # STEP 1: Exact model exists on disk, but in a SUBFOLDER!
            # (e.g. requested 'marigold_v2.safetensors', but stored in 'marigold/marigold_v2.safetensors')
            # -------------------------------------------------------------
            matched_val = None
            match_type = ""

            # Check available_vals for exact basename match (subfolder path)
            for opt in available_vals:
                if not isinstance(opt, str):
                    continue
                opt_norm = opt.replace("\\", "/")
                opt_base = os.path.basename(opt_norm).lower()
                if opt_base == req_base:
                    if opt_norm.lower() != clean_val_lower:
                        matched_val = opt
                        match_type = "exact_subfolder_match"
                        break

            # If not in available_vals, check disk indexer (strictly within compatible categories)
            disk_matches = indexer.basename_to_paths.get(req_base, [])
            if not matched_val and disk_matches:
                # Prioritize exact target category
                for cat, rel_p in disk_matches:
                    mapped_cat = map_fn(cat) if callable(map_fn) else cat
                    if (cat == target_cat or mapped_cat == target_cat) and rel_p.lower() != clean_val_lower:
                        matched_val = rel_p
                        match_type = "exact_category_subfolder"
                        break
                if not matched_val:
                    for cat, rel_p in disk_matches:
                        mapped_cat = map_fn(cat) if callable(map_fn) else cat
                        if (cat in compatible_cats_set or mapped_cat in compatible_cats_set) and rel_p.lower() != clean_val_lower:
                            matched_val = rel_p
                            match_type = f"cross_category_{cat}"
                            break

            if matched_val:
                # If matched_val exists in available_vals with different slash formatting, use the exact option string
                norm_matched = matched_val.replace("\\", "/").lower()
                for opt in available_vals:
                    if isinstance(opt, str) and opt.replace("\\", "/").lower() == norm_matched:
                        matched_val = opt
                        break

                # Only add if it's genuinely a different relative path (ignoring case & slashes)
                if matched_val.replace("\\", "/").lower() != clean_val_lower:
                    exact_resolved.append({
                        "nodeId": node_id,
                        "nodeKey": node_key,
                        "nodeTitle": node_title,
                        "parentSubgraphIds": entry.get("parentSubgraphIds", []),
                        "parentSubgraphKeys": entry.get("parentSubgraphKeys", []),
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

            # Normalized deduplicated candidate map: norm_path -> (preferred_opt, score)
            candidates_map = {}

            def _add_candidate(cand_path: str, score: float):
                if not cand_path or not isinstance(cand_path, str):
                    return
                cand_norm = cand_path.replace("\\", "/").strip()
                cand_key = cand_norm.lower()
                if cand_key == clean_val_lower:
                    return
                if cand_key in candidates_map:
                    prev_path, prev_score = candidates_map[cand_key]
                    if score > prev_score:
                        candidates_map[cand_key] = (prev_path, score)
                else:
                    candidates_map[cand_key] = (cand_path, score)

            # 2a. Check available options in widget
            if available_vals:
                for opt in available_vals:
                    if not isinstance(opt, str):
                        continue
                    opt_norm = opt.replace("\\", "/")
                    opt_base = os.path.basename(opt_norm).lower()
                    opt_s, opt_e = os.path.splitext(opt_base)
                    if opt_e not in VALID_MODEL_EXTENSIONS or opt_base == req_base:
                        continue
                    score = calculate_model_similarity(req_base, opt_base)
                    if score >= 0.55:
                        _add_candidate(opt, score)

            # 2b. Also search indexed disk models in the same category to guarantee fresh candidates
            try:
                sim_list = indexer.find_similar_models(cat_hint, current_val, folder_paths, top_k=5)
                for full_p, rel_p, score in sim_list:
                    if score >= 0.55:
                        # Prefer option string from available_vals if it matches
                        rel_norm = rel_p.replace("\\", "/").lower()
                        matching_opt = None
                        if available_vals:
                            for av in available_vals:
                                if isinstance(av, str) and av.replace("\\", "/").lower() == rel_norm:
                                    matching_opt = av
                                    break
                        cand_to_add = matching_opt if matching_opt else rel_p
                        _add_candidate(cand_to_add, score)
            except Exception:
                pass

            if candidates_map:
                sorted_cands = sorted(candidates_map.values(), key=lambda x: x[1], reverse=True)
                valid_cands = [
                    (opt, sc) for opt, sc in sorted_cands
                    if opt.replace("\\", "/").lower() != clean_val_lower
                ]
                if valid_cands:
                    best_cand, best_score = valid_cands[0]
                    alt_list = [{"model": opt, "score": round(sc * 100)} for opt, sc in valid_cands]
                    suggestions.append({
                        "nodeId": node_id,
                        "nodeKey": node_key,
                        "nodeTitle": node_title,
                        "parentSubgraphIds": entry.get("parentSubgraphIds", []),
                        "parentSubgraphKeys": entry.get("parentSubgraphKeys", []),
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

        # 2. Rescan disk models off the event loop thread
        indexer = SmartModelIndex.get_instance()
        await asyncio.to_thread(indexer.scan_all, folder_paths, True)

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

logger.info("[SmartModelResolver] ready (Subfolder Auto-Fix + Interactive Model Suggestions + Live Cache Refresh)")

if HAS_COMFY_V3:
    __all__ = ["SmartModelPathFinder", "WEB_DIRECTORY", "comfy_entrypoint"]
else:
    __all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY", "comfy_entrypoint"]
