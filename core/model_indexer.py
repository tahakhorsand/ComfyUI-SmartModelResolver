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

# Generic technical suffix tokens that should not count as model family identity
GENERIC_SUFFIX_TOKENS: Set[str] = {
    'int8', 'int4', 'int2', 'fp8', 'fp16', 'bf16', 'fp32', 'f32', 'f16', 'fp4',
    'convrot', 'scaled', 'pruned', 'unpruned', 'safetensors', 'ckpt', 'pt',
    'pth', 'bin', 'sft', 'onnx', 'gguf', 'e4m3fn', 'e5m2', 'emaonly', 'nonema', 'diffusers',
    'awq', 'nvfp4', 'mixed', 'comfy', 'comfyui'
}

KNOWN_MODEL_FAMILIES = [
    'gemma', 'qwen', 'flux', 'ltx', 'sdxl', 'sd', 'hunyuan', 'wan',
    'minimax', 'cogvideo', 'mochi', 'aura', 'kolors', 't5', 'clip',
    'siglip', 'eva02', 'vit', 'chameleon', 'deepseek', 'llama', 'mistral'
]

def extract_semantic_features(name: str) -> dict:
    name_clean = re.sub(r'\.(safetensors|ckpt|pt|pth|bin|sft|onnx|gguf)$', '', name.lower())
    raw_tokens = re.split(r'[-_.\s/]+', name_clean)
    tokens = [t for t in raw_tokens if t]

    sizes = set()
    families = set()
    filtered_tokens = set()

    for t in tokens:
        if re.match(r'^\d+(\.\d+)?b$', t):
            sizes.add(t)
            continue

        found_fam = False
        for kf in KNOWN_MODEL_FAMILIES:
            if t.startswith(kf) or kf in t:
                families.add(kf)
                found_fam = True
                break

        if not found_fam and t not in GENERIC_SUFFIX_TOKENS:
            filtered_tokens.add(t)

    return {
        'name_clean': name_clean,
        'tokens': set(tokens),
        'content_tokens': filtered_tokens,
        'sizes': sizes,
        'families': families
    }

def calculate_model_similarity(req_name: str, cand_name: str) -> float:
    req_f = extract_semantic_features(req_name)
    cand_f = extract_semantic_features(cand_name)

    seq_score = difflib.SequenceMatcher(None, req_f['name_clean'], cand_f['name_clean']).ratio()

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

    score = 0.50

    if req_f['sizes'] and cand_f['sizes']:
        if req_f['sizes'].intersection(cand_f['sizes']):
            score += 0.25
        else:
            score -= 0.10
    elif not req_f['sizes'] and not cand_f['sizes']:
        score += 0.08

    all_content = req_f['content_tokens'].union(cand_f['content_tokens'])
    if all_content:
        common_content = req_f['content_tokens'].intersection(cand_f['content_tokens'])
        jaccard = len(common_content) / len(all_content)
        score += jaccard * 0.20

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
                    cat_list = []
                    seen_rel = set()

                    # 1. Physical directory scan with os.walk
                    for d in dirs:
                        if not os.path.isdir(d):
                            continue
                        for root, subdirs, filenames in os.walk(d, followlinks=True):
                            subdirs[:] = [sd for sd in subdirs if sd != ".git" and not sd.startswith(".")]
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

                    # 2. Also incorporate any files returned by folder_paths.get_filename_list(cat)
                    try:
                        comfy_files = folder_paths.get_filename_list(cat)
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
            cat = folder_paths.map_legacy(cat) if hasattr(folder_paths, "map_legacy") else cat
            try:
                p = folder_paths.get_full_path(cat, rel)
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

    def find_similar_models(self, folder_name: str, requested_name: str, folder_paths, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """
        Looks for genuine SIMILAR model candidates (e.g. Gemma, Minimax, Qwen revisions/variants).
        Returns list of (full_path, rel_path, similarity_score) sorted descending by score.
        Strictly searches only compatible model categories.
        """
        if not requested_name or not isinstance(requested_name, str):
            return []

        clean_req = requested_name.strip().replace("\\", "/")
        req_base = os.path.basename(clean_req).lower()
        req_ext = os.path.splitext(req_base)[-1].lower()

        if req_ext and req_ext not in VALID_MODEL_EXTENSIONS:
            return []

        self.scan_all(folder_paths)
        folder_name = folder_paths.map_legacy(folder_name)

        compatible_map = {
            "text_encoders": ["text_encoders", "clip"],
            "clip": ["text_encoders", "clip"],
            "diffusion_models": ["diffusion_models", "unet", "checkpoints"],
            "unet": ["diffusion_models", "unet", "checkpoints"],
            "checkpoints": ["checkpoints", "diffusion_models"],
            "vae": ["vae", "vae_approx"],
            "loras": ["loras"],
            "controlnet": ["controlnet"],
            "upscale_models": ["upscale_models"],
        }

        search_cats = compatible_map.get(folder_name, [folder_name])
        candidates = []
        for cat in search_cats:
            mapped_cat = folder_paths.map_legacy(cat) if hasattr(folder_paths, "map_legacy") else cat
            if mapped_cat in self.cached_files_by_category:
                for rel_p in self.cached_files_by_category[mapped_cat]:
                    candidates.append((mapped_cat, rel_p))

        seen_rel = set()
        results = []

        for cat, rel_p in candidates:
            if rel_p in seen_rel:
                continue
            seen_rel.add(rel_p)

            cand_base = os.path.basename(rel_p).lower()
            if cand_base == req_base:
                continue

            score = calculate_model_similarity(req_base, cand_base)
            if score >= 0.58:
                try:
                    full_p = folder_paths.get_full_path(cat, rel_p)
                except Exception:
                    full_p = rel_p
                results.append((full_p, rel_p, score))

        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]

    def find_similar_model(self, folder_name: str, requested_name: str, folder_paths) -> Optional[Tuple[str, str, float]]:
        candidates = self.find_similar_models(folder_name, requested_name, folder_paths, top_k=1)
        return candidates[0] if candidates else None
