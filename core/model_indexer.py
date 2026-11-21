import os
import re
import time
import threading
import logging
import difflib
from typing import Optional, Tuple, List, Dict, Set

logger = logging.getLogger("SmartModelResolver")

# Strict set of valid model file extensions (NEVER match .py, .json, etc.)
VALID_MODEL_EXTENSIONS: Set[str] = {
    '.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.sft', '.onnx', '.gguf'
}

# Non-model ComfyUI folder_names_and_paths keys that must never be walked as model weights
NON_MODEL_CATEGORIES: Set[str] = {
    'custom_nodes', 'datasets', 'configs', 'diffusers', 'classifiers'
}

# Model categories that are architecturally compatible for fallback lookup / suggestions
COMPATIBLE_CATEGORIES: Dict[str, List[str]] = {
    'text_encoders': ['text_encoders', 'clip'],
    'clip': ['text_encoders', 'clip'],
    'diffusion_models': ['diffusion_models', 'unet', 'checkpoints'],
    'unet': ['diffusion_models', 'unet', 'checkpoints'],
    'checkpoints': ['checkpoints', 'diffusion_models', 'unet'],
    'vae': ['vae', 'vae_approx'],
    'vae_approx': ['vae', 'vae_approx'],
    'loras': ['loras'],
    'controlnet': ['controlnet'],
    'upscale_models': ['upscale_models'],
}


def get_compatible_categories(folder_name: str, folder_paths=None) -> List[str]:
    """Return deduplicated compatible ComfyUI categories for a given model category."""
    if not folder_name or folder_name == "ALL":
        return []
    map_fn = getattr(folder_paths, "map_legacy", None) if folder_paths is not None else None
    mapped = map_fn(folder_name) if callable(map_fn) else folder_name
    raw_cats = COMPATIBLE_CATEGORIES.get(mapped) or COMPATIBLE_CATEGORIES.get(folder_name) or [mapped]
    result: List[str] = []
    for cat in raw_cats:
        mc = map_fn(cat) if callable(map_fn) else cat
        if mc not in result:
            result.append(mc)
    return result

# Generic technical suffix tokens that should not count as model family identity
GENERIC_SUFFIX_TOKENS: Set[str] = {
    'int8', 'int4', 'int2', 'fp8', 'fp16', 'bf16', 'fp32', 'f32', 'f16', 'fp4',
    'convrot', 'scaled', 'pruned', 'unpruned', 'safetensors', 'ckpt', 'pt',
    'pth', 'bin', 'sft', 'onnx', 'gguf', 'e4m3fn', 'e5m2', 'emaonly', 'nonema', 'diffusers',
    'awq', 'nvfp4', 'mixed', 'comfy', 'comfyui'
}

PRIMARY_MODEL_FAMILIES = [
    'gemma', 'qwen', 'flux', 'ltx', 'sdxl', 'sd15', 'sd21', 'sd1', 'sd2', 'sd35', 'sd3', 'sd',
    'hunyuan', 'wan', 'minimax', 'cogvideo', 'mochi', 'aura', 'kolors',
    'chameleon', 'deepseek', 'llama', 'mistral'
]
PRIMARY_MODEL_FAMILIES_SET = set(PRIMARY_MODEL_FAMILIES)
COMPONENT_FAMILIES = ['t5', 'clip', 'siglip', 'eva02', 'vit']
KNOWN_MODEL_FAMILIES = PRIMARY_MODEL_FAMILIES + COMPONENT_FAMILIES


def _token_matches_family(token: str, kf: str) -> bool:
    """Match model family token using boundaries to avoid false substrings (e.g. swan->wan)."""
    if token == kf:
        return True
    if re.match(rf'^{re.escape(kf)}(?:\d|$)', token):
        return True
    if (kf == 't5' and token.startswith('t5xxl')) or (kf == 'ltx' and token.startswith('ltxv')):
        return True
    if len(kf) >= 5 and kf in token:
        return True
    return False


def extract_semantic_features(name: str) -> dict:
    name_clean = re.sub(r'\.(safetensors|ckpt|pt|pth|bin|sft|onnx|gguf)$', '', name.lower())
    name_clean = re.sub(r'sd[-_]xl', 'sdxl', name_clean)
    name_clean = re.sub(r'sd[-_.]?1[-_.]?5', 'sd15', name_clean)
    name_clean = re.sub(r'sd[-_.]?2[-_.]?1', 'sd21', name_clean)
    name_clean = re.sub(r'sd[-_.]?3[-_.]?5', 'sd35', name_clean)
    name_clean = re.sub(r'sd[-_.]?3(?!\d)', 'sd3', name_clean)

    # Split on separators while keeping decimal numbers like 1.3b or 2.5 intact
    raw_tokens = re.split(r'[-_\s/]+|(?<!\d)\.|(?<=\d)\.(?!\d)', name_clean)
    tokens = [t for t in raw_tokens if t]

    sizes = set()
    families = set()
    primary_families = set()
    filtered_tokens = set()

    for t in tokens:
        if re.match(r'^\d+(\.\d+)?b$', t):
            sizes.add(t)
            continue

        found_fam = False
        for kf in KNOWN_MODEL_FAMILIES:
            if _token_matches_family(t, kf):
                families.add(kf)
                if kf in PRIMARY_MODEL_FAMILIES_SET:
                    primary_families.add(kf)
                found_fam = True
                break

        if not found_fam and t not in GENERIC_SUFFIX_TOKENS:
            filtered_tokens.add(t)

    return {
        'name_clean': name_clean,
        'tokens': set(tokens),
        'content_tokens': filtered_tokens,
        'sizes': sizes,
        'families': families,
        'primary_families': primary_families
    }


def calculate_model_similarity(req_name: str, cand_name: str) -> float:
    req_f = extract_semantic_features(req_name)
    cand_f = extract_semantic_features(cand_name)

    seq_score = difflib.SequenceMatcher(None, req_f['name_clean'], cand_f['name_clean']).ratio()

    # Primary architecture mismatch always yields 0.0 even if both share a component tag like 'clip'
    if req_f['primary_families'] and cand_f['primary_families']:
        if not req_f['primary_families'].intersection(cand_f['primary_families']):
            return 0.0

    fam_match = False
    if req_f['families'] and cand_f['families']:
        if req_f['families'].intersection(cand_f['families']):
            fam_match = True
        else:
            return 0.0
    elif req_f['name_clean'][:4] == cand_f['name_clean'][:4] and len(req_f['name_clean']) >= 4:
        fam_match = True

    if not fam_match:
        return seq_score if seq_score >= 0.65 else 0.0

    score = 0.58

    if req_f['sizes'] and cand_f['sizes']:
        if req_f['sizes'].intersection(cand_f['sizes']):
            score += 0.20
        else:
            score -= 0.05
    elif not req_f['sizes'] and not cand_f['sizes']:
        score += 0.08

    all_content = req_f['content_tokens'].union(cand_f['content_tokens'])
    if all_content:
        common_content = req_f['content_tokens'].intersection(cand_f['content_tokens'])
        jaccard = len(common_content) / len(all_content)
        score += jaccard * 0.15

    score += seq_score * 0.15
    return min(0.99, max(0.0, score))

class SmartModelIndex:
    _instance = None

    def __init__(self):
        self.cached_files_by_category: Dict[str, List[str]] = {}  # category -> list of rel_paths
        self.basename_to_paths: Dict[str, List[Tuple[str, str]]] = {}  # lower_basename -> list of (cat, rel_path)
        self.last_scan_time = 0.0
        self.cache_ttl = 120.0  # seconds
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SmartModelIndex()
        return cls._instance

    def scan_all(self, folder_paths, force: bool = False):
        with self._lock:
            now = time.time()
            if not force and (now - self.last_scan_time < self.cache_ttl) and self.cached_files_by_category:
                return

            try:
                t0 = time.time()
                new_cached_files: Dict[str, List[str]] = {}
                new_basename_to_paths: Dict[str, List[Tuple[str, str]]] = {}

                folder_map = getattr(folder_paths, "folder_names_and_paths", {})
                for cat, (dirs, exts) in folder_map.items():
                    if cat in NON_MODEL_CATEGORIES:
                        continue
                    exts_set = {e.lower() for e in exts if isinstance(e, str)} if exts else set()
                    if not (exts_set & VALID_MODEL_EXTENSIONS):
                        continue

                    cat_list = []
                    seen_rel = set()

                    # 1. Physical directory scan with os.walk (with symlink cycle guard)
                    raw_get_filename_list = getattr(folder_paths, "_smr_orig_get_filename_list", folder_paths.get_filename_list)
                    for d in dirs:
                        if not os.path.isdir(d):
                            continue
                        try:
                            visited_real_dirs = {os.path.realpath(d)}
                        except Exception:
                            visited_real_dirs = set()
                        for root, subdirs, filenames in os.walk(d, followlinks=True):
                            next_subdirs = []
                            for sd in subdirs:
                                if sd == ".git" or sd.startswith("."):
                                    continue
                                try:
                                    real_sd = os.path.realpath(os.path.join(root, sd))
                                    if real_sd not in visited_real_dirs:
                                        visited_real_dirs.add(real_sd)
                                        next_subdirs.append(sd)
                                except Exception:
                                    continue
                            subdirs[:] = next_subdirs
                            for fn in filenames:
                                ext = os.path.splitext(fn)[-1].lower()
                                if ext in VALID_MODEL_EXTENSIONS:
                                    try:
                                        rel_p = os.path.relpath(os.path.join(root, fn), d).replace("\\", "/")
                                        if rel_p not in seen_rel:
                                            seen_rel.add(rel_p)
                                            cat_list.append(rel_p)
                                            base_lower = fn.lower()
                                            if base_lower not in new_basename_to_paths:
                                                new_basename_to_paths[base_lower] = []
                                            new_basename_to_paths[base_lower].append((cat, rel_p))
                                    except Exception:
                                        continue

                    # 2. Also incorporate files returned by the unhooked ComfyUI filename list (avoids stale cache feedback)
                    try:
                        comfy_files = raw_get_filename_list(cat)
                        for rel_p in comfy_files:
                            ext = os.path.splitext(rel_p)[-1].lower()
                            if ext in VALID_MODEL_EXTENSIONS:
                                norm_rel = rel_p.replace("\\", "/")
                                if norm_rel not in seen_rel:
                                    seen_rel.add(norm_rel)
                                    cat_list.append(norm_rel)
                                    base_lower = os.path.basename(norm_rel).lower()
                                    if base_lower not in new_basename_to_paths:
                                        new_basename_to_paths[base_lower] = []
                                    new_basename_to_paths[base_lower].append((cat, norm_rel))
                    except Exception:
                        pass

                    new_cached_files[cat] = sorted(cat_list)

                self.cached_files_by_category = new_cached_files
                self.basename_to_paths = new_basename_to_paths
                self.last_scan_time = time.time()
                total_count = sum(len(v) for v in new_cached_files.values())
                logger.info(f"[SmartModelResolver] Physical disk indexed {total_count} models across {len(new_cached_files)} categories in {time.time()-t0:.3f}s")
            except Exception as e:
                logger.error(f"[SmartModelResolver] Error during indexing: {e}")

    def find_model(self, folder_name: str, requested_name: str, folder_paths, allow_cross_category: bool = True) -> Optional[Tuple[str, str, str]]:
        """
        Locates the exact same model file if present in subfolders or (optionally) other categories.
        STRICT: Only matches the EXACT same basename.
        Returns: (full_path, rel_path, match_type) or None
        """
        if not requested_name or not isinstance(requested_name, str):
            return None

        clean_req = requested_name.strip().replace("\\", "/")
        req_base = os.path.basename(clean_req).lower()
        req_ext = os.path.splitext(req_base)[-1].lower()
        if req_ext and req_ext not in VALID_MODEL_EXTENSIONS:
            return None

        self.scan_all(folder_paths)
        raw_is_unrestricted = (not folder_name) or (folder_name == "ALL")
        map_fn = getattr(folder_paths, "map_legacy", None)
        mapped_folder = folder_name if raw_is_unrestricted else (map_fn(folder_name) if callable(map_fn) else folder_name)
        compatible_cats = set(get_compatible_categories(mapped_folder, folder_paths)) if not raw_is_unrestricted else set()
        raw_get_full_path = getattr(folder_paths, "_smr_orig_get_full_path", folder_paths.get_full_path)

        def _is_cat_allowed(cat: str) -> bool:
            if not allow_cross_category:
                return False
            if raw_is_unrestricted:
                return True
            mapped_cat = map_fn(cat) if callable(map_fn) else cat
            return mapped_cat in compatible_cats or cat in compatible_cats

        def _resolve_full(cat: str, rel: str) -> Optional[str]:
            cat = map_fn(cat) if callable(map_fn) else cat
            try:
                p = raw_get_full_path(cat, rel)
                if p and (os.path.isfile(p) or os.path.islink(p)):
                    return p
            except Exception:
                pass
            # Physical disk fallback
            folder_map = getattr(folder_paths, "folder_names_and_paths", {})
            if cat in folder_map:
                dirs, _ = folder_map[cat]
                clean_rel = rel.replace("/", os.sep).replace("\\", os.sep)
                for d in dirs:
                    cand = os.path.join(d, clean_rel)
                    if os.path.isfile(cand) or os.path.islink(cand):
                        return cand
            return None

        def _match_from_list(matches: List[Tuple[str, str]]) -> Optional[Tuple[str, str, str]]:
            # Prioritize exact target category
            if not raw_is_unrestricted:
                for cat, rel_p in matches:
                    mapped_cat = map_fn(cat) if callable(map_fn) else cat
                    if cat == mapped_folder or mapped_cat == mapped_folder:
                        full_p = _resolve_full(cat, rel_p)
                        if full_p:
                            return full_p, rel_p, "exact_category_subfolder"
            # Compatible cross-category fallback (or unrestricted when folder_name in ("", "ALL"))
            for cat, rel_p in matches:
                if _is_cat_allowed(cat):
                    full_p = _resolve_full(cat, rel_p)
                    if full_p:
                        return full_p, rel_p, f"cross_category_{cat}"
            return None

        # 1. Exact basename match
        if req_base in self.basename_to_paths:
            hit = _match_from_list(self.basename_to_paths[req_base])
            if hit:
                return hit

        # 2. Extension omitted in query
        if not req_ext:
            for ext in VALID_MODEL_EXTENSIONS:
                cand = f"{req_base}{ext}"
                if cand in self.basename_to_paths:
                    hit = _match_from_list(self.basename_to_paths[cand])
                    if hit:
                        return hit

        return None

    def find_similar_models(self, folder_name: str, requested_name: str, folder_paths, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """
        Looks for genuine SIMILAR model candidates (e.g. Gemma, Minimax, Qwen revisions/variants).
        Returns list of (full_path, rel_path, similarity_score) sorted descending by score.
        Strictly searches only compatible model categories (or all categories when folder_name == 'ALL').
        """
        if not requested_name or not isinstance(requested_name, str):
            return []

        clean_req = requested_name.strip().replace("\\", "/")
        req_base = os.path.basename(clean_req).lower()
        req_ext = os.path.splitext(req_base)[-1].lower()

        if req_ext and req_ext not in VALID_MODEL_EXTENSIONS:
            return []

        raw_is_all = (folder_name == "ALL")
        self.scan_all(folder_paths)
        folder_name = folder_name if raw_is_all else folder_paths.map_legacy(folder_name)

        search_cats = list(self.cached_files_by_category.keys()) if raw_is_all else get_compatible_categories(folder_name, folder_paths)
        candidates = []
        for cat in search_cats:
            mapped_cat = folder_paths.map_legacy(cat) if hasattr(folder_paths, "map_legacy") else cat
            if mapped_cat in self.cached_files_by_category:
                for rel_p in self.cached_files_by_category[mapped_cat]:
                    candidates.append((mapped_cat, rel_p))

        raw_get_full_path = getattr(folder_paths, "_smr_orig_get_full_path", folder_paths.get_full_path)
        seen_rel = set()
        results = []

        for cat, rel_p in candidates:
            if (cat, rel_p) in seen_rel:
                continue
            seen_rel.add((cat, rel_p))

            cand_base = os.path.basename(rel_p).lower()
            if cand_base == req_base:
                continue

            score = calculate_model_similarity(req_base, cand_base)
            if score >= 0.55:
                try:
                    full_p = raw_get_full_path(cat, rel_p)
                except Exception:
                    full_p = rel_p
                results.append((full_p or rel_p, rel_p, score))

        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]

    def find_similar_model(self, folder_name: str, requested_name: str, folder_paths) -> Optional[Tuple[str, str, float]]:
        candidates = self.find_similar_models(folder_name, requested_name, folder_paths, top_k=1)
        return candidates[0] if candidates else None
