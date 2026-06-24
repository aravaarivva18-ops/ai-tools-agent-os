---
name: comfyui-workflow-generation
description: Guidelines for developing, editing, and validating ComfyUI photo and video generation workflows with character consistency.
---

# ComfyUI Workflow Generation & Integration

## 🛠️ Stack & Config
- **Base Engines**: SDXL (Juggernaut XL v9 Lightning) for Photo; SD 1.5 (DreamShaper 8) for Video.
- **Identity & Consistency**: InstantID, IP-Adapter FaceID Plus v2, LivePortrait (facial expression transfer).
- **Motion & Temporal Stability**: AnimateDiff Evolved (v3 LCM), ControlNet OpenPose, ControlNet Tile/Temporal.
- **Post-processing & Scale**: FaceDetailer (Impact Pack), FILM (Frame Interpolation), Ultimate SD Upscale (4x-UltraSharp).

## 📐 Best Practices & Code Patterns

### 1. Model Loading vs. Application (IP-Adapter)
- **Do not use** the deprecated `IPAdapterApply` node.
- **Unified Loader**: Use `IPAdapterUnifiedLoader` to load models and automatic companion LoRAs (set preset, e.g. `"FACEID PLUS V2"`). Note that the loader only outputs `MODEL` and `IPADAPTER`.
- **Application**: Always chain the output of the loader into `IPAdapterAdvanced` to apply the reference image to the model pipeline.
  ```python
  # Correct connection flow:
  # Checkpoint -> AnimateDiff -> IPAdapterUnifiedLoader -> IPAdapterAdvanced (with image input) -> KSampler
  ```

### 2. Facial Animation Pipeline (LivePortrait)
- To animate a face using a reference video, you must build the complete detection, cropping, and stitching pipeline:
  1. Load models via `DownloadAndLoadLivePortraitModels` (outputs `pipeline`).
  2. Load face cropper via `LivePortraitLoadCropper` (outputs `cropper`).
  3. Crop reference face via `LivePortraitCropper` (inputs `pipeline`, `cropper`, and reference image; outputs `cropped_image` and `crop_info`).
  4. Process animation via `LivePortraitProcess` (inputs `pipeline`, `cropped_image`, `crop_info`, and driving video frames).
  5. **Stitching**: Ensure `stitching = True` is set in the process node to composite the animated face back onto the full frames.

### 3. Workflow Management
- Avoid editing ComfyUI `.json` files manually to prevent link mismatches.
- Use the programmatic python builder `generate_workflows.py` located in `tools/` to modify the node coordinate layouts, input/output connections, and widget values, then re-compile the JSON files.

## ⚠️ Common Pitfalls & Anti-patterns
- **Error**: Connecting `IPAdapterUnifiedLoader` directly to KSampler inputs without `IPAdapterAdvanced` (fails to transfer the face).
- **Error**: Skipping `LivePortraitCropper` and passing an uncropped image to `LivePortraitProcess` (causes execution crash due to missing `crop_info`).
- **Error**: Connecting legacy output slots like `"animated_images"` on `LivePortraitProcess` (correct output slot name is `"IMAGE"`).

## 🔄 Verification Checklist
1. Validate JSON loadability: `python3 -c "import json; json.load(open('workflow.json'))"`.
2. Cross-reference model filenames in widgets with paths inside [setup-and-models-guide.md](file:///Users/rus/ai-tools/vault/comfyui/setup-and-models-guide.md).
3. Ensure all connection links map to valid, existing node inputs and outputs.
