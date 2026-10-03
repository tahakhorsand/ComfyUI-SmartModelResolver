# ComfyUI-SmartModelResolver

An intelligent, non-intrusive model locator and subfolder auto-linker for **ComfyUI**.

Eliminates workflow loading failures, missing subfolder paths, and red widget errors with a modern, glassmorphic UI.

---

## ✨ Features

- **🔍 Automatic Subfolder Resolution**:
  Seamlessly maps models saved without subfolders (e.g. `marigold_v2_normals.safetensors`) to their actual local path (e.g. `marigold/marigold_v2_normals.safetensors`).
- **💡 Smart Model Suggestions**:
  When a workflow requests a model you do not have (e.g. `minimax_h3_ref2va_pruned...`), the extension locates authentic alternatives in your library (e.g. `minimax_h3_ref2va...` with 90%+ match) and asks you politely via a sleek notification card.
- **🚫 Zero Workflow Blocking**:
  No invasive modal windows or blocking overlays. All notifications float non-intrusively in the top corner with `pointer-events: none` on the backdrop, keeping your canvas completely interactive.
- **🪟 Modern Glassmorphic Design**:
  Translucent glass cards with backdrop blur, glowing cyan accents, and clear status badges.
- **🧩 Full Subgraph / Group Node Support**:
  Recursively traverses both root graphs and inner subgraphs, keeping promoted inputs and internal definitions perfectly in sync.
- **🛡️ Strict Model File Protection**:
  Only recognizes authentic neural model formats (`.safetensors`, `.ckpt`, `.pt`, `.pth`, `.bin`, `.sft`). Never matches scripts, configs, or non-model files.

---

## 🚀 Installation

1. Open a terminal inside your ComfyUI `custom_nodes` directory:
   ```bash
   git clone https://github.com/tahakhorsand/ComfyUI-SmartModelResolver
   ```
2. Restart ComfyUI.
3. Open any workflow. If models are in subfolders or close alternatives exist, the glassmorphic assistant will appear in the top-right corner.

---

## ⚙️ How It Works

1. **Backend Interceptor**: Transparently hooks into `folder_paths.get_full_path` to resolve paths on-the-fly during execution without breaking native ComfyUI caching.
2. **Frontend Sync**: Calls ComfyUI's internal `app.refreshMissingModels()` after linking to immediately clear red error highlights from the canvas and the Issues sidebar.

---

## 📄 License
MIT License
