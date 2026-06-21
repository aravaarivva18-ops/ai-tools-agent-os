# DOX Contract — YouTube Faceless Pipeline

- This folder contains components for automatic script writing, voiceover/scene generation, image rendering, and video creation/uploading.
- The pipeline serves as a tool to automate faceless channel content generation.

## ⚙️ Module Responsibilities

- **content_gen.py**: Scriptwriting and visual prompt design for scenes.
- **seo_optimizer.py**: Automatic optimization of titles, tags, and description for the niche.
- **upload_cli.py**: CLI tool to automate video uploading to YouTube API.
- **ui/**: Streamlit-based interface for visual control and editing of the generation process.

## 📐 Guidelines

- Always ensure visual concept generation (`generate_image`) runs gracefully with a local Pillow fallback when offline.
- Validate output formats (scripts, tags, and scenes) using clean validation logic.
- Prevent syntax errors and format issues before reloading the pipeline server.
