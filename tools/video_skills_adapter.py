#!/usr/bin/env python3
"""Video Skills Adapter for Remotion programming video production ecosystem."""

import logging
import os
import subprocess  # nosec B404

logger = logging.getLogger(__name__)


class VideoSkillsAdapter:
    """Provides functionality to configure and render Remotion videos."""

    def __init__(self, workspace_path: str = "/Users/rus/ai-tools"):
        self.workspace_path = workspace_path

    def init_remotion_project(self, project_name: str) -> bool:
        """Scaffolds a blank Remotion project using create-video CLI."""
        cmd = [
            "npx",
            "create-video@latest",
            "--yes",
            "--blank",
            "--no-tailwind",
            project_name,
        ]
        try:
            result = subprocess.run(  # nosec B603
                cmd,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug("Remotion validate failed for %s: %s", self.workspace_path, e)
            return False

    def configure_composition(
        self,
        project_path: str,
        comp_id: str,
        width: int,
        height: int,
        fps: int,
        duration_in_frames: int,
    ) -> bool:
        """Configures Composition settings in src/Root.tsx file."""
        root_file_path = os.path.join(project_path, "src", "Root.tsx")
        if not os.path.exists(root_file_path):
            # If Root.tsx doesn't exist, create a basic one
            os.makedirs(os.path.dirname(root_file_path), exist_ok=True)
            content = f"""import {{ Composition }} from "remotion";

export const RemotionRoot = () => {{
  return (
    <Composition
      id="{comp_id}"
      durationInFrames={{ {duration_in_frames} }}
      fps={{ {fps} }}
      width={{ {width} }}
      height={{ {height} }}
    />
  );
}};
"""
            with open(root_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        with open(root_file_path, encoding="utf-8") as f:
            content = f.read()

        # Update attributes using regex replacements
        content = re_replace_attr(content, "id", f'"{comp_id}"')
        content = re_replace_attr(content, "width", f"{{{width}}}")
        content = re_replace_attr(content, "height", f"{{{height}}}")
        content = re_replace_attr(content, "fps", f"{{{fps}}}")
        content = re_replace_attr(
            content, "durationInFrames", f"{{{duration_in_frames}}}"
        )

        with open(root_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    def render_video(self, project_path: str, comp_id: str, output_path: str) -> bool:
        """Renders the video composition using Remotion CLI."""
        cmd = ["npx", "remotion", "render", comp_id, output_path]
        try:
            result = subprocess.run(  # nosec B603
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug("Remotion render failed for %s: %s", comp_id, e)
            return False

    def render_still(
        self, project_path: str, comp_id: str, output_path: str, frame: int = 0
    ) -> bool:
        """Renders a single frame composition using Remotion CLI."""
        cmd = [
            "npx",
            "remotion",
            "still",
            comp_id,
            output_path,
            f"--frame={frame}",
        ]
        try:
            result = subprocess.run(  # nosec B603
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug("Remotion still render failed for %s: %s", comp_id, e)
            return False


def re_replace_attr(content: str, attr: str, value: str) -> str:
    """Helper method to replace Composition JSX attributes in Root.tsx."""
    import re

    pattern = rf"{attr}=\{{?[^ \n}}]+\}}?"
    replacement = f"{attr}={value}"
    if re.search(pattern, content):
        return re.sub(pattern, replacement, content)
    # If attribute is not found, insert it inside the Composition tag
    return content.replace("<Composition", f"<Composition\n      {replacement}")
