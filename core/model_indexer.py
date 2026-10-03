import os
import re
import time
import logging
import difflib
from typing import Optional, Tuple, List, Dict, Set

logger = logging.getLogger("SmartModelResolver")

# Strict set of valid model file extensions (NEVER match .py, .json, etc.)
VALID_MODEL_EXTENSIONS: Set[str] = {
    '.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.sft'
}

class SmartModelIndex:
    _instance = None

    def __init__(self):
        self.cached_files_by_category: Dict[str, List[Tuple[str, str]]] = {}  # category -> list of (rel_path, full_path)
        self.basename_to_paths: Dict[str, List[Tuple[str, str, str]]] = {}     # lower_basename -> list of (category, rel_path, full_path)
        self.last_scan_time = 0.0
        self.cache_ttl = 10.0  # seconds
        self._dir_mtimes: Dict[str, float] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SmartModelIndex()
        return cls._instance

    def _should_rescan(self, folder_paths) -> bool:
        now = time.time()
        if now - self.last_scan_time < self.cache_ttl:
            return False

        for cat, (paths, _) in folder_paths.folder_names_and_paths.items():
            for p in paths:
                if os.path.isdir(p):
                    try:
                        mtime = os.path.getmtime(p)
                        if self._dir_mtimes.get(p) != mtime:
                            return True
                    except OSError:
                        pass
        return False

    def scan_all(self, folder_paths, force: bool = False):
        if not force and not self._should_rescan(folder_paths) and self.cached_files_by_category:
            return

        t0 = time.time()
        new_cached_files: Dict[str, List[Tuple[str, str]]] = {}
        new_basename_to_paths: Dict[str, List[Tuple[str, str, str]]] = {}
        new_dir_mtimes: Dict[str, float] = {}

        for cat, (paths, exts) in folder_paths.folder_names_and_paths.items():
            cat_list = []
            for root_dir in paths:
                if not os.path.isdir(root_dir):
                    continue
                try:
                    new_dir_mtimes[root_dir] = os.path.getmtime(root_dir)
                except OSError:
                    pass

                for dirpath, _, filenames in os.walk(root_dir, followlinks=True):
                    for fname in filenames:
                        ext = os.path.splitext(fname)[-1].lower()
                        # Strictly enforce valid model extensions
                        if ext not in VALID_MODEL_EXTENSIONS:
                            continue
                        if exts and ext not in exts and "" not in exts:
                            continue

                        full_p = os.path.join(dirpath, fname)
                        try:
                            rel_p = os.path.relpath(full_p, root_dir).replace("\\", "/")
                        except ValueError:
                            rel_p = fname

                        cat_list.append((rel_p, full_p))
                        base_lower = fname.lower()
                        if base_lower not in new_basename_to_paths:
                            new_basename_to_paths[base_lower] = []
                        new_basename_to_paths[base_lower].append((cat, rel_p, full_p))

            new_cached_files[cat] = cat_list

        self.cached_files_by_category = new_cached_files
        self.basename_to_paths = new_basename_to_paths
        self._dir_mtimes = new_dir_mtimes
        self.last_scan_time = time.time()
        logger.info(f"[SmartModelResolver] Scanned & indexed {sum(len(v) for v in new_cached_files.values())} model files across {len(new_cached_files)} categories in {time.time()-t0:.2f}s")

    def find_model(self, folder_name: str, requested_name: str, folder_paths) -> Optional[Tuple[str, str, str]]:
        """
        Locates the exact same model file if present in subfolders or other categories.
        STRICT: Only matches the EXACT same basename.
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

        # 1. Exact basename match
        if req_base in self.basename_to_paths:
            matches = self.basename_to_paths[req_base]
            for cat, rel_p, full_p in matches:
                if cat == folder_name:
                    return full_p, rel_p, "exact_category_subfolder"
            for cat, rel_p, full_p in matches:
                return full_p, rel_p, f"cross_category_{cat}"

        # 2. Extension omitted in query
        if not req_ext:
            for ext in VALID_MODEL_EXTENSIONS:
                cand = f"{req_base}{ext}"
                if cand in self.basename_to_paths:
                    matches = self.basename_to_paths[cand]
                    for cat, rel_p, full_p in matches:
                        if cat == folder_name:
                            return full_p, rel_p, "exact_category_subfolder"
                    for cat, rel_p, full_p in matches:
                        return full_p, rel_p, f"cross_category_{cat}"

        return None

    def find_similar_model(self, folder_name: str, requested_name: str, folder_paths) -> Optional[Tuple[str, str, float]]:
        """
        Looks for a genuine SIMILAR model candidate (e.g. 2509 vs 2511, or slightly different revision).
        Strictly restricted to authentic model files in relevant categories.
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

        # Candidates to compare: prioritize same category
        candidates = []
        if folder_name in self.cached_files_by_category:
            for rel_p, full_p in self.cached_files_by_category[folder_name]:
                candidates.append((rel_p, full_p))

        # Also include diffusion_models / unet if relevant
        if folder_name in ("unet", "diffusion_models"):
            for other_cat in ("diffusion_models", "unet", "checkpoints"):
                if other_cat != folder_name and other_cat in self.cached_files_by_category:
                    for rel_p, full_p in self.cached_files_by_category[other_cat]:
                        candidates.append((rel_p, full_p))

        best_candidate = None
        best_score = 0.0

        # Tokenize requested name
        clean_req_tokens = set(re.findall(r'[a-zA-Z0-9]+', req_stem))

        for rel_p, full_p in candidates:
            cand_base = os.path.basename(rel_p).lower()
            cand_stem, cand_ext = os.path.splitext(cand_base)

            if cand_ext not in VALID_MODEL_EXTENSIONS:
                continue

            # Don't suggest exact matches here (those are handled by find_model)
            if cand_base == req_base:
                continue

            cand_tokens = set(re.findall(r'[a-zA-Z0-9]+', cand_stem))
            # Must share at least 2 common tokens or primary family prefix
            common = clean_req_tokens.intersection(cand_tokens)
            if len(common) < 2 and not (req_stem[:6] == cand_stem[:6] and len(req_stem) > 6):
                continue

            # Calculate string similarity ratio
            score = difflib.SequenceMatcher(None, req_stem, cand_stem).ratio()
            if score > best_score:
                best_score = score
                best_candidate = (full_p, rel_p, score)

        if best_candidate and best_score >= 0.65:
            return best_candidate

        return None
