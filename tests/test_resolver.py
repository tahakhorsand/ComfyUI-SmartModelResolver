import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch

# Add ComfyUI and custom_node root to sys.path
COMFY_ROOT = os.path.abspath(r"E:\ComfyUI\ComfyUI")
NODE_ROOT = os.path.join(COMFY_ROOT, "custom_nodes", "ComfyUI-SmartModelResolver")

if COMFY_ROOT not in sys.path:
    sys.path.insert(0, COMFY_ROOT)
if NODE_ROOT not in sys.path:
    sys.path.insert(0, NODE_ROOT)

import folder_paths
import importlib
smr = importlib.import_module("custom_nodes.ComfyUI-SmartModelResolver")
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

            with patch("execution.validate_inputs", side_effect=mock_orig):
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

            with patch("execution.validate_inputs", side_effect=mock_orig):
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

                with patch("execution.validate_prompt", side_effect=mock_orig_prompt):
                    await smr.smart_validate_prompt(prompt_id, prompt)
                    # Input value should be auto-aligned to the matching backslash option
                    self.assertEqual(prompt["10"]["inputs"]["ckpt_name"], "subfolder\\model.safetensors")

        asyncio.run(run_test())

    def test_smart_get_full_path_subfolder_and_absolute(self):
        # 1. Absolute path check
        abs_p = os.path.abspath(__file__)
        self.assertEqual(smr.smart_get_full_path("checkpoints", abs_p), abs_p)

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
                self.assertIn("sub_model.gguf", indexer.basename_to_paths)


if __name__ == "__main__":
    unittest.main()
