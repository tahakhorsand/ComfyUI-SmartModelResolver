import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch

# Add ComfyUI and current repository root to sys.path
COMFY_ROOT = os.path.abspath(r"E:\ComfyUI\ComfyUI")
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if COMFY_ROOT not in sys.path:
    sys.path.insert(0, COMFY_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import folder_paths
import importlib.util
spec = importlib.util.spec_from_file_location("smart_model_resolver", os.path.join(REPO_ROOT, "__init__.py"))
smr = importlib.util.module_from_spec(spec)
sys.modules["smart_model_resolver"] = smr
spec.loader.exec_module(smr)

SmartModelIndex = smr.SmartModelIndex
VALID_MODEL_EXTENSIONS = smr.VALID_MODEL_EXTENSIONS
GENERIC_SUFFIX_TOKENS = smr.GENERIC_SUFFIX_TOKENS
from core.model_indexer import (
    calculate_model_similarity,
    extract_semantic_features
)


class TestModelIndexer(unittest.TestCase):
    def test_gguf_support(self):
        self.assertIn('.gguf', VALID_MODEL_EXTENSIONS)
        self.assertIn('gguf', GENERIC_SUFFIX_TOKENS)

        features = extract_semantic_features("flux1-dev-Q4_K_M.gguf")
        self.assertEqual(features['name_clean'], "flux1-dev-q4_k_m")
        self.assertIn('flux', features['families'])

    def test_similarity_scoring(self):
        # Flux variant
        s1 = calculate_model_similarity("flux1-dev.safetensors", "flux1-schnell.safetensors")
        self.assertGreater(s1, 0.50)

        # Incompatible families
        s2 = calculate_model_similarity("sdxl_base.safetensors", "flux1-dev.safetensors")
        self.assertEqual(s2, 0.0)

        # GGUF models
        s3 = calculate_model_similarity("sd3.5_large.safetensors", "sd3.5_large.gguf")
        self.assertGreater(s3, 0.70)

    def test_subfolder_exact_match(self):
        import time
        indexer = SmartModelIndex()
        indexer.last_scan_time = time.time()  # Prevent scan_all from overwriting test fixture
        indexer.cached_files_by_category = {
            "checkpoints": ["anime/v1-5-pruned.safetensors", "flux/flux1-dev.safetensors"]
        }
        indexer.basename_to_paths = {
            "v1-5-pruned.safetensors": [("checkpoints", "anime/v1-5-pruned.safetensors")],
            "flux1-dev.safetensors": [("checkpoints", "flux/flux1-dev.safetensors")]
        }

        mock_folder_paths = MagicMock()
        mock_folder_paths.map_legacy.side_effect = lambda x: x
        mock_folder_paths.get_full_path.side_effect = lambda cat, rel: f"/mock/models/{cat}/{rel}"

        with patch("os.path.isfile", return_value=True):
            res = indexer.find_model("checkpoints", "v1-5-pruned.safetensors", mock_folder_paths)
            self.assertIsNotNone(res)
            full_p, rel_p, match_type = res
            self.assertEqual(rel_p, "anime/v1-5-pruned.safetensors")
            self.assertEqual(match_type, "exact_category_subfolder")


class TestCacheRefreshAndHooks(unittest.TestCase):
    def test_refresh_cache_clears_comfy_caches(self):
        # Setup dummy stale cache in folder_paths
        folder_paths.filename_list_cache["test_stale_cat"] = (["dummy.safetensors"], {}, 123.0)
        if hasattr(folder_paths, "cache_helper") and folder_paths.cache_helper is not None:
            folder_paths.cache_helper.active = True
            folder_paths.cache_helper.set("test_stale_cat", (["dummy.safetensors"], {}, 123.0))

        # Call refresh endpoint implementation
        async def run_refresh():
            req = MagicMock()
            resp = await smr._handle_refresh_cache_impl(req)
            return resp

        resp = asyncio.run(run_refresh())
        self.assertEqual(resp.status, 200)

        # Stale entry must be cleared
        self.assertNotIn("test_stale_cat", folder_paths.filename_list_cache)
        if hasattr(folder_paths, "cache_helper") and folder_paths.cache_helper is not None:
            self.assertIsNone(folder_paths.cache_helper.get("test_stale_cat"))

    def test_smart_validate_inputs_suppresses_verified_files(self):
        # Verify that smart_validate_inputs removes value_not_in_list for existing files
        async def run_test():
            prompt_id = "test_prompt_1"
            prompt = {
                "3": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": "existing_model.safetensors"}
                }
            }
            item = "3"
            validated = {}

            # Mock _orig_validate_inputs to simulate value_not_in_list error
            async def mock_orig(pid, pr, itm, val, vis=None):
                reasons = [{
                    "type": "value_not_in_list",
                    "message": "Value not in list",
                    "details": "existing_model.safetensors not in []",
                    "extra_info": {
                        "input_name": "ckpt_name",
                        "received_value": "existing_model.safetensors"
                    }
                }]
                return (False, reasons, itm)

            with patch.object(smr, "_orig_validate_inputs", side_effect=mock_orig):
                with patch.object(smr, "check_file_exists_any_category", return_value=True):
                    # Call smart_validate_inputs
                    res = await smr.smart_validate_inputs(prompt_id, prompt, item, validated)
                    # Should be converted to valid True!
                    self.assertTrue(res[0])
                    self.assertEqual(len(res[1]), 0)
                    self.assertEqual(res[2], item)

        asyncio.run(run_test())

    def test_smart_validate_inputs_preserves_genuine_missing_files(self):
        async def run_test():
            prompt_id = "test_prompt_2"
            prompt = {
                "3": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": "completely_missing.safetensors"}
                }
            }
            item = "3"
            validated = {}

            async def mock_orig(pid, pr, itm, val, vis=None):
                reasons = [{
                    "type": "value_not_in_list",
                    "message": "Value not in list",
                    "details": "completely_missing.safetensors not in []",
                    "extra_info": {
                        "input_name": "ckpt_name",
                        "received_value": "completely_missing.safetensors"
                    }
                }]
                return (False, reasons, itm)

            with patch.object(smr, "_orig_validate_inputs", side_effect=mock_orig):
                with patch.object(smr, "check_file_exists_any_category", return_value=False):
                    with patch("os.path.isfile", return_value=False):
                        with patch.object(SmartModelIndex.get_instance(), "find_model", return_value=None):
                            res = await smr.smart_validate_inputs(prompt_id, prompt, item, validated)
                            # Must fail for real missing models!
                            self.assertFalse(res[0])
                            self.assertEqual(len(res[1]), 1)
                            self.assertEqual(res[1][0]["type"], "value_not_in_list")

        asyncio.run(run_test())


    def test_smart_validate_prompt_auto_aligns_slashes(self):
        async def run_test():
            prompt_id = "test_prompt_slash"
            # Node specifies a model with forward slashes
            prompt = {
                "10": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": "subfolder/model.safetensors"}
                }
            }

            # Mock class INPUT_TYPES returning backslash options on Windows
            mock_class = MagicMock()
            mock_class.INPUT_TYPES.return_value = {
                "required": {
                    "ckpt_name": (["subfolder\\model.safetensors"],)
                }
            }

            import nodes
            with patch.dict(nodes.NODE_CLASS_MAPPINGS, {"CheckpointLoaderSimple": mock_class}):
                async def mock_orig_prompt(pid, pr, part=None):
                    return (True, None, ["10"], {})

                with patch.object(smr, "_orig_validate_prompt", side_effect=mock_orig_prompt):
                    await smr.smart_validate_prompt(prompt_id, prompt)
                    # Input value should be auto-aligned to the matching backslash option
                    self.assertEqual(prompt["10"]["inputs"]["ckpt_name"], "subfolder\\model.safetensors")

        asyncio.run(run_test())

    def test_smart_get_full_path_subfolder_and_absolute(self):
        # 1a. Absolute path check succeeds ONLY for valid model extensions
        abs_model = os.path.abspath(r"C:\models\custom_model.safetensors")
        with patch("os.path.isfile", side_effect=lambda p: p == abs_model):
            self.assertEqual(smr.smart_get_full_path("checkpoints", abs_model), abs_model)

        # 1b. Absolute path check rejects non-model files (e.g. .py)
        abs_py = os.path.abspath(__file__)
        self.assertIsNone(smr.smart_get_full_path("checkpoints", abs_py))

        # 1c. Path traversal (..) is strictly rejected
        self.assertIsNone(smr.smart_get_full_path("checkpoints", "../../secret.safetensors"))

        # 2. Subfolder auto-location via indexer
        with patch.object(smr.SmartModelIndex, "find_model", return_value=(r"C:\models\sub\v1.safetensors", r"sub\v1.safetensors", "exact")):
            res = smr.smart_get_full_path("checkpoints", "v1.safetensors")
            self.assertEqual(res, r"C:\models\sub\v1.safetensors")

    def test_supported_pt_extensions_includes_gguf(self):
        self.assertIn(".gguf", folder_paths.supported_pt_extensions)

    def test_smart_get_filename_list_combines_indexer(self):
        indexer = SmartModelIndex.get_instance()
        indexer.cached_files_by_category["checkpoints"] = ["subfolder/test_model.safetensors"]

        mock_orig = MagicMock(return_value=["root_model.safetensors"])
        with patch.object(smr, "_orig_get_filename_list", mock_orig):
            result = smr.smart_get_filename_list("checkpoints")
            self.assertIn("root_model.safetensors", result)
            expected_sub = "subfolder\\test_model.safetensors" if os.sep == "\\" else "subfolder/test_model.safetensors"
            self.assertIn(expected_sub, result)

    def test_scan_all_physical_walk(self):
        indexer = SmartModelIndex()
        mock_folder_paths = MagicMock()
        mock_folder_paths.folder_names_and_paths = {
            "checkpoints": ([r"C:\mock_checkpoints"], {".safetensors", ".gguf"})
        }
        mock_folder_paths.get_filename_list.return_value = []

        mock_walk_data = [
            (r"C:\mock_checkpoints", ["sub"], ["root_model.safetensors"]),
            (r"C:\mock_checkpoints\sub", [], ["sub_model.gguf"])
        ]
        with patch("os.path.isdir", return_value=True):
            with patch("os.walk", return_value=mock_walk_data):
                indexer.scan_all(mock_folder_paths, force=True)
                ckpts = indexer.cached_files_by_category.get("checkpoints", [])
                self.assertIn("root_model.safetensors", ckpts)
                self.assertIn("sub/sub_model.gguf", ckpts)
class TestV3NodeAndEntrypoint(unittest.TestCase):
    def test_v3_node_schema_and_execute(self):
        SmartModelPathFinder = smr.SmartModelPathFinder
        if smr.HAS_COMFY_V3:
            schema = SmartModelPathFinder.define_schema()
            self.assertIsNotNone(schema)
            self.assertEqual(schema.node_id, "SmartModelPathFinder")
            self.assertEqual(schema.category, "SmartModelResolver")
            self.assertFalse(hasattr(smr, "NODE_CLASS_MAPPINGS"))

        # Test execute without throwing allow_fuzzy unexpected keyword error
        with patch.object(smr.SmartModelIndex, "find_model", return_value=(r"C:\models\sub\m.safetensors", r"sub\m.safetensors", "exact")):
            res = SmartModelPathFinder.execute("m.safetensors", "ALL", allow_fuzzy=True)
            self.assertTrue(res[2])

    def test_v1_or_v3_node_execution_and_validation(self):
        SmartModelPathFinder = smr.SmartModelPathFinder
        if smr.HAS_COMFY_V3:
            # Pure V3 class must NOT define legacy V1 'resolve' or custom FUNCTION='resolve'
            self.assertEqual(SmartModelPathFinder.FUNCTION, "EXECUTE_NORMALIZED")
            import nodes, execution
            prompt = {
                "1": {
                    "class_type": "SmartModelPathFinder",
                    "inputs": {"model_name": "test.safetensors", "category": "ALL", "allow_fuzzy": True}
                }
            }
            validated = {}
            with patch.dict(nodes.NODE_CLASS_MAPPINGS, {"SmartModelPathFinder": SmartModelPathFinder}):
                res = asyncio.run(execution.validate_inputs("pid_v3", prompt, "1", validated))
                self.assertEqual(res, (True, [], "1"))
        else:
            inputs = SmartModelPathFinder.INPUT_TYPES()
            self.assertIn("required", inputs)
            self.assertIn("model_name", inputs["required"])
            inst = SmartModelPathFinder()
            with patch.object(smr.SmartModelIndex, "find_model", return_value=(r"C:\models\sub\m.safetensors", r"sub\m.safetensors", "exact")):
                full_p, rel_p, found, info = inst.resolve("m.safetensors", "ALL", allow_fuzzy=True)
                self.assertTrue(found)
                self.assertEqual(full_p, r"C:\models\sub\m.safetensors")

    def test_comfy_entrypoint_exported(self):
        self.assertTrue(hasattr(smr, "comfy_entrypoint"))
        ext = asyncio.run(smr.comfy_entrypoint())
        if smr.HAS_COMFY_V3:
            self.assertIsNotNone(ext)
            nodes_list = asyncio.run(ext.get_node_list())
            self.assertEqual(len(nodes_list), 1)
            self.assertIs(nodes_list[0], smr.SmartModelPathFinder)


class TestBatchResolverSafety(unittest.TestCase):
    def test_healthy_model_never_suggested_or_resolved(self):
        """
        Verify that if a healthy model from the same family exists on disk,
        it is NEVER included in resolved or suggestions, even if an entry is sent.
        """
        async def run_test():
            req_data = {
                "entries": [
                    {
                        "nodeId": "10",
                        "nodeTitle": "Load CLIP",
                        "widgetName": "clip_name",
                        "currentValue": "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
                        "availableValues": ["gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"]
                    }
                ]
            }
            mock_request = MagicMock()
            async def get_json():
                return req_data
            mock_request.json = get_json

            resp = await smr._handle_resolve_batch_impl(mock_request)
            self.assertEqual(resp.status, 200)
            import json
            body = json.loads(resp.body.decode())
            self.assertEqual(len(body.get("resolved", [])), 0)
            self.assertEqual(len(body.get("suggestions", [])), 0)

        asyncio.run(run_test())

    def test_similar_family_replaces_only_missing_model(self):
        """
        Verify that missing gemma4_e2b suggests gemma4_e4b, while healthy gemma4-12b is ignored.
        """
        async def run_test():
            req_data = {
                "entries": [
                    {
                        "nodeId": "10",
                        "nodeTitle": "Main Load CLIP",
                        "widgetName": "clip_name",
                        "currentValue": "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
                        "availableValues": [
                            "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
                            "gemma4_e4b_it_fp8_scaled.safetensors"
                        ]
                    },
                    {
                        "nodeId": "15",
                        "nodeTitle": "Prompt Enhance Load CLIP",
                        "widgetName": "clip_name",
                        "currentValue": "gemma4_e2b_it_int8_convrot.safetensors",
                        "availableValues": [
                            "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
                            "gemma4_e4b_it_fp8_scaled.safetensors"
                        ]
                    }
                ]
            }
            mock_request = MagicMock()
            async def get_json():
                return req_data
            mock_request.json = get_json

            with patch.object(smr, "check_file_exists_any_category", side_effect=lambda fp, val, **kw: "12b" in val):
                resp = await smr._handle_resolve_batch_impl(mock_request)
                self.assertEqual(resp.status, 200)
                import json
                body = json.loads(resp.body.decode())
                # Node 10 (healthy) must NOT appear anywhere
                all_node_ids = [r["nodeId"] for r in body.get("resolved", [])] + [s["nodeId"] for s in body.get("suggestions", [])]
                self.assertNotIn("10", all_node_ids)
                # Node 15 (missing) must have a suggestion
                self.assertIn("15", all_node_ids)

        asyncio.run(run_test())

    def test_similar_candidates_no_duplicates_from_slashes_or_categories(self):
        """
        Verify that slash variants (e.g. Qwen\\model.safetensors vs Qwen/model.safetensors)
        do not produce duplicate suggestions in the alternatives list.
        """
        async def run_test():
            req_data = {
                "entries": [
                    {
                        "nodeId": "20",
                        "nodeTitle": "Load CLIP",
                        "widgetName": "clip_name",
                        "currentValue": "qwen_3_4b.safetensors",
                        "availableValues": [
                            "Qwen\\qwen_4b_ace15.safetensors",
                            "Qwen\\qwen3vl_4b_fp8_scaled.safetensors"
                        ]
                    }
                ]
            }
            mock_request = MagicMock()
            async def get_json():
                return req_data
            mock_request.json = get_json

            # Mock indexer returning the forward slash variants
            mock_indexer = MagicMock()
            mock_indexer.find_model.return_value = None
            mock_indexer.find_similar_models.return_value = [
                ("/path/Qwen/qwen_4b_ace15.safetensors", "Qwen/qwen_4b_ace15.safetensors", 0.85),
                ("/path/Qwen/qwen3vl_4b_fp8_scaled.safetensors", "Qwen/qwen3vl_4b_fp8_scaled.safetensors", 0.83),
            ]
            mock_indexer.basename_to_paths = {}

            with patch.object(smr.SmartModelIndex, "get_instance", return_value=mock_indexer):
                with patch.object(smr, "check_file_exists_any_category", return_value=False):
                    resp = await smr._handle_resolve_batch_impl(mock_request)
                    self.assertEqual(resp.status, 200)
                    import json
                    body = json.loads(resp.body.decode())
                    suggs = body.get("suggestions", [])
                    self.assertEqual(len(suggs), 1)
                    alts = suggs[0].get("alternatives", [])
                    alt_models = [a["model"].replace("\\", "/").lower() for a in alts]
                    # Must contain no duplicates!
                    self.assertEqual(len(alt_models), len(set(alt_models)))
                    self.assertEqual(len(alt_models), 2)

        asyncio.run(run_test())

    def test_subfolder_model_not_suppressed_by_step0(self):
        """Verify that a model residing in a subfolder (e.g. Flux/ae.safetensors)
        is NOT suppressed by STEP 0 and is cleanly returned in resolved."""
        async def run_test():
            req_data = {
                "entries": [
                    {
                        "nodeId": "10",
                        "nodeTitle": "Text to Image (Z-Image-Turbo)",
                        "widgetName": "vae_name",
                        "currentValue": "ae.safetensors",
                        "availableValues": [
                            "Flux\\ae.safetensors",
                            "sdxl_vae.safetensors"
                        ]
                    }
                ]
            }
            mock_request = MagicMock()
            async def get_json():
                return req_data
            mock_request.json = get_json

            with patch.object(smr, "check_file_exists_any_category", return_value=False):
                with patch.object(smr, "_orig_get_full_path", return_value=None):
                    resp = await smr._handle_resolve_batch_impl(mock_request)
                    self.assertEqual(resp.status, 200)
                    import json
                    body = json.loads(resp.body.decode())
                    resolved = body.get("resolved", [])
                    self.assertEqual(len(resolved), 1)
                    self.assertEqual(resolved[0]["nodeId"], "10")
                    self.assertEqual(resolved[0]["widgetName"], "vae_name")
                    self.assertEqual(resolved[0]["originalValue"], "ae.safetensors")
                    self.assertEqual(resolved[0]["resolvedValue"], "Flux\\ae.safetensors")
                    self.assertEqual(resolved[0]["matchType"], "exact_subfolder_match")

        asyncio.run(run_test())

    def test_family_aware_similarity(self):
        """Verify that variants within the same family are suggested,
        while conflicting families are strictly blocked with 0.0 score."""
        # Same family variants
        s_qwen = calculate_model_similarity("qwen_3_4b.safetensors", "qwen_2.5_3b_instruct.safetensors")
        self.assertGreaterEqual(s_qwen, 0.55)

        s_sdxl = calculate_model_similarity("sd_xl_base_1.0.safetensors", "sdxl_lightning_8step.safetensors")
        self.assertGreaterEqual(s_sdxl, 0.55)

        s_flux = calculate_model_similarity("flux1-dev.safetensors", "flux1-schnell.safetensors")
        self.assertGreaterEqual(s_flux, 0.55)

        # Cross-family conflicts (MUST be 0.0!)
        self.assertEqual(calculate_model_similarity("sd_xl_base_1.0.safetensors", "v1-5-pruned-emaonly.safetensors"), 0.0)
        self.assertEqual(calculate_model_similarity("sd_xl_base_1.0.safetensors", "flux1-dev.safetensors"), 0.0)
        self.assertEqual(calculate_model_similarity("gemma_2_2b.safetensors", "qwen_2.5_3b_instruct.safetensors"), 0.0)
        self.assertEqual(calculate_model_similarity("flux_clip_l.safetensors", "sdxl_clip_g.safetensors"), 0.0)

    def test_family_boundary_prevents_false_substrings(self):
        """Words containing short substrings like swan->wan, gravity->vit, sde->sd must NOT misclassify."""
        self.assertNotIn("wan", extract_semantic_features("swan_v1.safetensors")["families"])
        self.assertNotIn("vit", extract_semantic_features("gravity_v1.safetensors")["families"])
        self.assertNotIn("sd", extract_semantic_features("sde_sampler.safetensors")["families"])

    def test_scan_all_drops_deleted_models_no_ghost_cache(self):
        """Deleted files must not survive scan_all(force=True) via smart_get_filename_list feedback."""
        indexer = SmartModelIndex.get_instance()
        indexer.cached_files_by_category = {"checkpoints": ["deleted_ghost.safetensors"]}

        mock_fp = MagicMock()
        mock_fp.folder_names_and_paths = {"checkpoints": ([r"C:\empty_ckpts"], {".safetensors"})}
        mock_fp._smr_orig_get_filename_list = MagicMock(return_value=[])
        # Even if folder_paths.get_filename_list would return the old cached item, _smr_orig is used!
        mock_fp.get_filename_list = MagicMock(side_effect=lambda cat: list(indexer.cached_files_by_category.get(cat, [])))

        with patch("os.path.isdir", return_value=False):
            indexer.scan_all(mock_fp, force=True)
            self.assertNotIn("deleted_ghost.safetensors", indexer.cached_files_by_category.get("checkpoints", []))

    def test_smart_get_full_path_no_recursion_on_stale_entry(self):
        """A stale entry pointing to a missing file must return None cleanly without RecursionError."""
        import time
        indexer = SmartModelIndex.get_instance()
        old_cache = indexer.cached_files_by_category
        old_basename = indexer.basename_to_paths
        old_time = indexer.last_scan_time
        try:
            indexer.last_scan_time = time.time()
            indexer.cached_files_by_category = {"checkpoints": ["sub/ghost.safetensors"]}
            indexer.basename_to_paths = {"ghost.safetensors": [("checkpoints", "sub/ghost.safetensors")]}
            with patch.object(smr, "_orig_get_full_path", return_value=None):
                with patch.object(folder_paths, "_smr_orig_get_full_path", return_value=None):
                    with patch("os.path.isfile", return_value=False), patch("os.path.islink", return_value=False):
                        res = smr.smart_get_full_path("checkpoints", "ghost.safetensors")
                        self.assertIsNone(res)
        finally:
            indexer.cached_files_by_category = old_cache
            indexer.basename_to_paths = old_basename
            indexer.last_scan_time = old_time

    def test_scan_all_symlink_cycle_terminates(self):
        """scan_all must prune already-visited real directories to prevent symlink cycle loops."""
        indexer = SmartModelIndex()
        mock_fp = MagicMock()
        mock_fp.folder_names_and_paths = {"checkpoints": ([r"C:\root_dir"], {".safetensors"})}
        mock_fp._smr_orig_get_filename_list = MagicMock(return_value=[])

        def fake_walk(d, followlinks=True):
            subdirs = ["loop_link"]
            yield (r"C:\root_dir", subdirs, ["m1.safetensors"])
            # Because realpath of loop_link maps back to C:\root_dir, subdirs must be pruned!
            if "loop_link" in subdirs:
                yield (r"C:\root_dir\loop_link", ["loop_link"], ["m1.safetensors"])

        with patch("os.path.isdir", return_value=True):
            with patch("os.walk", side_effect=fake_walk):
                with patch("os.path.realpath", side_effect=lambda p: r"C:\root_dir" if p.endswith("root_dir") or p.endswith("loop_link") else p):
                    indexer.scan_all(mock_fp, force=True)
                    ckpts = indexer.cached_files_by_category.get("checkpoints", [])
                    self.assertEqual(ckpts, ["m1.safetensors"])

    def test_smart_model_path_finder_all_fuzzy_and_strict_category(self):
        """SmartModelPathFinder with category='ALL' searches all categories for fuzzy matches,
        while explicit category='loras' disables cross-category fallback."""
        import time
        SmartModelPathFinder = smr.SmartModelPathFinder
        indexer = SmartModelIndex.get_instance()
        old_cache = indexer.cached_files_by_category
        old_basename = indexer.basename_to_paths
        old_time = indexer.last_scan_time
        try:
            indexer.last_scan_time = time.time()
            indexer.cached_files_by_category = {
                "checkpoints": ["flux1-dev.safetensors"],
                "loras": ["flux_lora_v1.safetensors"],
            }
            indexer.basename_to_paths = {
                "flux1-dev.safetensors": [("checkpoints", "flux1-dev.safetensors")],
                "flux_lora_v1.safetensors": [("loras", "flux_lora_v1.safetensors")],
            }
            with patch("os.path.isfile", return_value=True):
                with patch.object(folder_paths, "_smr_orig_get_full_path", side_effect=lambda c, r: f"/mock/{c}/{r}"):
                    # Explicit category='loras' must NOT match checkpoint 'flux1-dev.safetensors'
                    res_strict = SmartModelPathFinder.execute("flux1-dev.safetensors", "loras", allow_fuzzy=False)
                    self.assertFalse(res_strict[2])

                    # category='ALL' + allow_fuzzy=True must find fuzzy LoRA across categories
                    res_all = SmartModelPathFinder.execute("flux_lora_v2.safetensors", "ALL", allow_fuzzy=True)
                    self.assertTrue(res_all[2])
                    self.assertEqual(res_all[1], "flux_lora_v1.safetensors")
        finally:
            indexer.cached_files_by_category = old_cache
            indexer.basename_to_paths = old_basename
            indexer.last_scan_time = old_time

    def test_resolve_batch_ignores_extensionless_and_echoes_node_key(self):
        """Extensionless non-model settings (e.g. bicubic, flux prompt) must be skipped; nodeKey must be echoed."""
        async def run_test():
            req_data = {
                "entries": [
                    {
                        "nodeId": "1",
                        "nodeKey": "5#1",
                        "nodeTitle": "Image Scale",
                        "widgetName": "upscale_method",
                        "currentValue": "bicubic",
                        "availableValues": ["nearest-exact", "bilinear", "bicubic"]
                    },
                    {
                        "nodeId": "2",
                        "nodeKey": "5#2",
                        "nodeTitle": "CLIP Text Encode",
                        "widgetName": "clip_text",
                        "currentValue": "flux",
                        "availableValues": []
                    },
                    {
                        "nodeId": "10",
                        "nodeKey": "5#10",
                        "nodeTitle": "Load VAE",
                        "widgetName": "vae_name",
                        "currentValue": "ae.safetensors",
                        "availableValues": ["Flux\\ae.safetensors"]
                    }
                ]
            }
            mock_request = MagicMock()
            async def get_json():
                return req_data
            mock_request.json = get_json

            with patch.object(smr, "check_file_exists_any_category", return_value=False):
                with patch.object(smr, "_orig_get_full_path", return_value=None):
                    resp = await smr._handle_resolve_batch_impl(mock_request)
                    self.assertEqual(resp.status, 200)
                    import json
                    body = json.loads(resp.body.decode())
                    self.assertEqual(len(body.get("resolved", [])), 1)
                    self.assertEqual(len(body.get("suggestions", [])), 0)
                    self.assertEqual(body["resolved"][0]["nodeKey"], "5#10")

        asyncio.run(run_test())

    def test_smart_validate_inputs_ignores_extensionless_strings(self):
        """smart_validate_inputs must NOT suppress value_not_in_list for extensionless non-model values."""
        async def run_test():
            prompt = {"3": {"class_type": "Upscale", "inputs": {"upscale_method": "bicubic"}}}
            validated = {}

            async def mock_orig(pid, pr, itm, val, vis=None):
                return (False, [{
                    "type": "value_not_in_list",
                    "message": "Value not in list",
                    "extra_info": {"input_name": "upscale_method", "received_value": "bicubic"}
                }], itm)

            with patch.object(smr, "_orig_validate_inputs", side_effect=mock_orig):
                with patch.object(smr, "check_file_exists_any_category", return_value=True):
                    res = await smr.smart_validate_inputs("pid", prompt, "3", validated)
                    self.assertFalse(res[0])
                    self.assertEqual(len(res[1]), 1)

        asyncio.run(run_test())

    def test_smart_validate_inputs_preserves_upstream_failure(self):
        """Downstream / output nodes must NOT be flipped to valid when upstream failed."""
        async def run_test():
            # Case 1: _orig_validate_inputs returns (False, [], "9") because upstream failed
            prompt1 = {"9": {"class_type": "SaveImage", "inputs": {"images": ["3", 0]}}}
            validated1 = {"3": (False, [{"type": "missing", "message": "err", "details": ""}], "3")}

            async def mock_orig_empty_reasons(pid, pr, itm, val, vis=None):
                return (False, [], itm)

            with patch.object(smr, "_orig_validate_inputs", side_effect=mock_orig_empty_reasons):
                res1 = await smr.smart_validate_inputs("pid1", prompt1, "9", validated1)
                self.assertEqual(res1, (False, [], "9"))

            # Case 2: Downstream node has BOTH failed upstream ["3", 0] AND a bypassed value_not_in_list
            prompt2 = {
                "5": {
                    "class_type": "LoraLoader",
                    "inputs": {"model": ["3", 0], "lora_name": "valid_lora.safetensors"}
                }
            }
            validated2 = {"3": (False, [{"type": "error", "message": "upstream bad", "details": ""}], "3")}

            async def mock_orig_bypassed_reason(pid, pr, itm, val, vis=None):
                return (False, [{
                    "type": "value_not_in_list",
                    "message": "Value not in list",
                    "extra_info": {"input_name": "lora_name", "received_value": "valid_lora.safetensors"}
                }], itm)

            with patch.object(smr, "_orig_validate_inputs", side_effect=mock_orig_bypassed_reason):
                with patch.object(smr, "check_file_exists_any_category", return_value=True):
                    res2 = await smr.smart_validate_inputs("pid2", prompt2, "5", validated2)
                    self.assertFalse(res2[0])
                    self.assertEqual(res2[1], [])
                    self.assertFalse(validated2["5"][0])

        asyncio.run(run_test())

    def test_scan_all_skips_non_model_categories(self):
        """custom_nodes, datasets, configs, diffusers, and classifiers must be skipped by scan_all."""
        indexer = SmartModelIndex()
        mock_fp = MagicMock()
        mock_fp._smr_orig_get_filename_list = MagicMock(return_value=[])
        mock_fp.folder_names_and_paths = {
            "checkpoints": ([r"C:\mock_ckpts"], {".safetensors"}),
            "custom_nodes": ([r"C:\mock_custom_nodes"], set()),
            "datasets": ([r"C:\mock_datasets"], set()),
            "configs": ([r"C:\mock_configs"], [".yaml"]),
            "diffusers": ([r"C:\mock_diffusers"], ["folder"]),
            "classifiers": ([r"C:\mock_classifiers"], {""}),
        }
        with patch("os.path.isdir", return_value=True):
            with patch("os.walk", return_value=[(r"C:\any", [], ["some_weight.safetensors"])]):
                indexer.scan_all(mock_fp, force=True)
                self.assertIn("checkpoints", indexer.cached_files_by_category)
                for ignored_cat in ("custom_nodes", "datasets", "configs", "diffusers", "classifiers"):
                    self.assertNotIn(ignored_cat, indexer.cached_files_by_category)

    def test_cross_category_isolation(self):
        """Incompatible categories (checkpoints vs loras/vae) must never cross-resolve; compatible ones still do."""
        import time
        indexer = SmartModelIndex()
        indexer.last_scan_time = time.time()
        indexer.cached_files_by_category = {
            "checkpoints": ["sub/ckpt_only.safetensors"],
            "text_encoders": ["sub/clip_model.safetensors"],
        }
        indexer.basename_to_paths = {
            "ckpt_only.safetensors": [("checkpoints", "sub/ckpt_only.safetensors")],
            "clip_model.safetensors": [("text_encoders", "sub/clip_model.safetensors")],
        }
        mock_fp = MagicMock()
        mock_fp.map_legacy.side_effect = lambda x: {"clip": "text_encoders", "unet": "diffusion_models"}.get(x, x)
        mock_fp._smr_orig_get_full_path.side_effect = lambda c, r: f"/mock/{c}/{r}"
        mock_fp.folder_names_and_paths = {
            "checkpoints": ([r"C:\ckpts"], {".safetensors"}),
            "loras": ([r"C:\loras"], {".safetensors"}),
            "vae": ([r"C:\vae"], {".safetensors"}),
            "text_encoders": ([r"C:\te"], {".safetensors"}),
        }

        with patch.object(smr.SmartModelIndex, "get_instance", return_value=indexer):
            with patch("os.path.isfile", side_effect=lambda p: ("\\ckpts\\" in p or "\\te\\" in p or "/checkpoints/" in p or "/text_encoders/" in p)):
                # Incompatible: checkpoint must NOT satisfy loras or vae
                self.assertIsNone(indexer.find_model("loras", "ckpt_only.safetensors", mock_fp, allow_cross_category=True))
                self.assertIsNone(indexer.find_model("vae", "ckpt_only.safetensors", mock_fp, allow_cross_category=True))
                with patch.object(smr, "_orig_get_full_path", return_value=None):
                    with patch.object(smr, "folder_paths", mock_fp):
                        self.assertIsNone(smr.smart_get_full_path("loras", "sub/ckpt_only.safetensors"))

                # Compatible: text_encoders satisfies clip
                hit = indexer.find_model("clip", "clip_model.safetensors", mock_fp, allow_cross_category=True)
                self.assertIsNotNone(hit)
                self.assertEqual(hit[1], "sub/clip_model.safetensors")

            # Batch resolver STEP 0 & STEP 1 must also block checkpoint resolving as lora
            async def run_batch():
                req_data = {
                    "entries": [
                        {
                            "nodeId": "40",
                            "nodeTitle": "Load LoRA",
                            "widgetName": "lora_name",
                            "currentValue": "ckpt_only.safetensors",
                            "availableValues": [],
                        }
                    ]
                }
                req = MagicMock()
                async def get_json():
                    return req_data
                req.json = get_json

                with patch.object(smr, "_orig_get_full_path", return_value=None):
                    with patch.object(smr, "check_file_exists_any_category", return_value=False):
                        resp = await smr._handle_resolve_batch_impl(req)
                        import json
                        body = json.loads(resp.body.decode())
                        self.assertEqual(body.get("resolved", []), [])

            asyncio.run(run_batch())

    def test_reimport_does_not_double_wrap_hooks(self):
        """Re-loading __init__.py must preserve the original unhooked ComfyUI functions."""
        import execution
        orig_full = folder_paths._smr_orig_get_full_path
        orig_list = folder_paths._smr_orig_get_filename_list
        orig_vp = execution._smr_orig_validate_prompt
        orig_vi = execution._smr_orig_validate_inputs

        self.assertIsNot(orig_full, smr.smart_get_full_path)
        self.assertIsNot(orig_list, smr.smart_get_filename_list)
        self.assertIsNot(orig_vp, smr.smart_validate_prompt)
        self.assertIsNot(orig_vi, smr.smart_validate_inputs)

        # Simulate a second module import (e.g. ComfyUI reload / sys.modules miss)
        spec2 = importlib.util.spec_from_file_location("smart_model_resolver_reimport", os.path.join(REPO_ROOT, "__init__.py"))
        smr2 = importlib.util.module_from_spec(spec2)
        sys.modules["smart_model_resolver_reimport"] = smr2
        try:
            spec2.loader.exec_module(smr2)
            self.assertIs(smr2._orig_get_full_path, orig_full)
            self.assertIs(smr2._orig_get_filename_list, orig_list)
            self.assertIs(smr2._orig_validate_prompt, orig_vp)
            self.assertIs(smr2._orig_validate_inputs, orig_vi)
        finally:
            # Restore primary module hooks cleanly
            folder_paths.get_full_path = smr.smart_get_full_path
            folder_paths.get_filename_list = smr.smart_get_filename_list
            execution.validate_prompt = smr.smart_validate_prompt
            execution.validate_inputs = smr.smart_validate_inputs
            sys.modules.pop("smart_model_resolver_reimport", None)

    def test_decimal_sizes_and_dotted_sd_versions(self):
        """Decimal parameter counts (1.3b) and dotted SD versions (sd3.5, sd1.5) must be extracted accurately."""
        feats_wan = extract_semantic_features("wan2.1_t2v_1.3B.safetensors")
        self.assertIn("1.3b", feats_wan["sizes"])
        self.assertNotIn("3b", feats_wan["sizes"])
        self.assertIn("wan", feats_wan["families"])

        self.assertGreaterEqual(calculate_model_similarity("sd3.5_large.safetensors", "sd35_large.safetensors"), 0.55)
        self.assertGreaterEqual(calculate_model_similarity("sd1.5_base.safetensors", "sd15_base.safetensors"), 0.55)
        self.assertEqual(calculate_model_similarity("sd3.5_large.safetensors", "sd1.5_base.safetensors"), 0.0)


if __name__ == "__main__":
    unittest.main()

