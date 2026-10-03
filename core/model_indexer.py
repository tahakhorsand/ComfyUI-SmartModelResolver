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
    '.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.sft'
}

# Generic technical suffix tokens that should not count as model family identity
GENERIC_SUFFIX_TOKENS: Set[str] = {
    'int8', 'int4', 'int2', 'fp8', 'fp16', 'bf16', 'fp32', 'f32', 'f16',
    'convrot', 'scaled', 'pruned', 'unpruned', 'safetensors', 'ckpt', 'pt',
    'pth', 'bin', 'sft', 'e4m3fn', 'e5m2', 'emaonly', 'nonema', 'diffusers'
}

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

                all_cats = list(getattr(folder_paths, "folder_names_and_paths", {}).keys())
                for cat in all_cats:
                    try:
                        files = folder_paths.get_filename_list(cat)
                    except Exception:
                        continue

                    cat_list = []
                    for rel_p in files:
                        ext = os.path.splitext(rel_p)[-1].lower()
                        if ext not in VALID_MODEL_EXTENSIONS:
                            continue
                        norm_rel = rel_p.replace("\\", "/")
                        cat_list.append(norm_rel)
                        base_lower = os.path.basename(norm_rel).lower()
                        if base_lower not in new_basename_to_paths:
                            new_basename_to_paths[base_lower] = []
                        new_basename_to_paths[base_lower].append((cat, norm_rel))

                    new_cached_files[cat] = cat_list

                self.cached_files_by_category = new_cached_files
                self.basename_to_paths = new_basename_to_paths
                self.last_scan_time = time.time()
                total_count = sum(len(v) for v in new_cached_files.values())
                logger.info(f"[SmartModelResolver] Fast-indexed {total_count} models across {len(new_cached_files)} categories in {time.time()-t0:.3f}s")
            except Exception as e:
                logger.error(f"[SmartModelResolver] Error during indexing: {e}")

    def find_model(self, folder_name: str, requested_name: str, folder_paths) -> Optional[Tuple[str, str, str]]:
        """
        Locates the exact same model file if present in subfolders or other categories.
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
        folder_name = folder_paths.map_legacy(folder_name)

        def _resolve_full(cat: str, rel: str) -> Optional[str]:
            try:
                p = folder_paths.get_full_path(cat, rel)
                if p and (os.path.isfile(p) or os.path.islink(p)):
                    return p
            except Exception:
                pass
            return None

        # 1. Exact basename match
        if req_base in self.basename_to_paths:
            matches = self.basename_to_paths[req_base]
            # Prioritize target category
            for cat, rel_p in matches:
                if cat == folder_name:
                    full_p = _resolve_full(cat, rel_p)
                    if full_p:
                        return full_p, rel_p, "exact_category_subfolder"
            # Cross-category fallback
            for cat, rel_p in matches:
                full_p = _resolve_full(cat, rel_p)
                if full_p:
                    return full_p, rel_p, f"cross_category_{cat}"

        # 2. Extension omitted in query
        if not req_ext:
            for ext in VALID_MODEL_EXTENSIONS:
                cand = f"{req_base}{ext}"
                if cand in self.basename_to_paths:
                    matches = self.basename_to_paths[cand]
                    for cat, rel_p in matches:
                        if cat == folder_name:
                            full_p = _resolve_full(cat, rel_p)
                            if full_p:
                                return full_p, rel_p, "exact_category_subfolder"
                    for cat, rel_p in matches:
                        full_p = _resolve_full(cat, rel_p)
                        if full_p:
                            return full_p, rel_p, f"cross_category_{cat}"

        return None

    def find_similar_model(self, folder_name: str, requested_name: str, folder_paths) -> Optional[Tuple[str, str, float]]:
        """
        Looks for a genuine SIMILAR model candidate (e.g. Gemma, Minimax, Qwen revisions/variants).
        Strictly requires matching at least one model identity token (not generic int8/fp8 tags).
        Returns (full_path, rel_path, similarity_score) or None.
        """
        if not requested_name or not isinstance(requested_name, str):
            return None

        clean_req = requested_name.strip().replace("\\", "/")
        req_base = os.path.basename(clean_req).lower()
        req_stem, req_ext = os.path.splitext(req_base)

        if req_ext and req_ext not in VALID_MODEL_EXTENSIONS:
            return None

        self.scan_all(folder_paths)
        folder_name = folder_paths.map_legacy(folder_name)

        # Candidates pool: search primary category first
        candidates = []
        if folder_name in self.cached_files_by_category:
            for rel_p in self.cached_files_by_category[folder_name]:
                candidates.append((folder_name, rel_p))

        # Also search other key categories (text_encoders, diffusion_models, checkpoints, loras)
        key_cats = ["text_encoders", "diffusion_models", "checkpoints", "loras", "vae"]
        for cat in key_cats:
            if cat != folder_name and cat in self.cached_files_by_category:
                for rel_p in self.cached_files_by_category[cat]:
                    candidates.append((cat, rel_p))

        best_candidate = None
        best_score = 0.0

        clean_req_tokens = set(re.findall(r'[a-zA-Z0-9]+', req_stem))
        req_identity = clean_req_tokens - GENERIC_SUFFIX_TOKENS

        for cat, rel_p in candidates:
            cand_base = os.path.basename(rel_p).lower()
            cand_stem, cand_ext = os.path.splitext(cand_base)

            if cand_ext not in VALID_MODEL_EXTENSIONS:
                continue

            # Don't suggest exact matches here (those are handled by find_model)
            if cand_base == req_base:
                continue

            cand_tokens = set(re.findall(r'[a-zA-Z0-9]+', cand_stem))
            cand_identity = cand_tokens - GENERIC_SUFFIX_TOKENS

            # Must share at least one genuine model identity token or 5-char prefix
            common_identity = req_identity.intersection(cand_identity)
            if not common_identity and not (req_stem[:5] == cand_stem[:5] and len(req_stem) > 4):
                continue

            # Calculate string similarity ratio
            score = difflib.SequenceMatcher(None, req_stem, cand_stem).ratio()
            if score > best_score:
                best_score = score
                try:
                    full_p = folder_paths.get_full_path(cat, rel_p)
                except Exception:
                    full_p = rel_p
                best_candidate = (full_p, rel_p, score)

        if best_candidate and best_score >= 0.58:
            return best_candidate

        return None
