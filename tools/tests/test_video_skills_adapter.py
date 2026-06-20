import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from video_skills_adapter import VideoSkillsAdapter


def test_video_skills_adapter_init():
    """Test VideoSkillsAdapter initialization with correct paths."""
    adapter = VideoSkillsAdapter(workspace_path="dummy_workspace")
    assert adapter.workspace_path == "dummy_workspace"


def test_init_remotion_project_cmd(monkeypatch):
    """Test that project setup command is correctly constructed and invoked."""
    adapter = VideoSkillsAdapter(workspace_path="dummy_workspace")
    mock_run = MagicMock()
    monkeypatch.setattr("subprocess.run", mock_run)

    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "success"

    success = adapter.init_remotion_project("my-video")
    assert success
    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    assert "npx" in args[0]
    assert "create-video@latest" in args[0]
    assert "my-video" in args[0]


def test_configure_composition_edits_file():
    """Test that configure_composition correctly updates or creates Root.tsx with props."""
    with tempfile.TemporaryDirectory() as temp_dir:
        src_dir = os.path.join(temp_dir, "src")
        os.makedirs(src_dir)
        root_file = os.path.join(src_dir, "Root.tsx")

        # Initial Root.tsx contents
        initial_content = """import { Composition } from "remotion";
export const RemotionRoot = () => {
  return (
    <Composition
      id="OldComp"
      durationInFrames={100}
      fps={30}
      width={1080}
      height={1080}
    />
  );
};
"""
        with open(root_file, "w", encoding="utf-8") as f:
            f.write(initial_content)

        adapter = VideoSkillsAdapter(workspace_path=temp_dir)
        success = adapter.configure_composition(
            project_path=temp_dir,
            comp_id="NewB2BReport",
            width=1920,
            height=1080,
            fps=60,
            duration_in_frames=300,
        )

        assert success
        with open(root_file, encoding="utf-8") as f:
            updated_content = f.read()

        assert 'id="NewB2BReport"' in updated_content
        assert "width={1920}" in updated_content
        assert "height={1080}" in updated_content
        assert "fps={60}" in updated_content
        assert "durationInFrames={300}" in updated_content


def test_render_video_cmd(monkeypatch):
    """Test that render_video command runs the correct CLI render arguments."""
    adapter = VideoSkillsAdapter(workspace_path="dummy_workspace")
    mock_run = MagicMock()
    monkeypatch.setattr("subprocess.run", mock_run)

    mock_run.return_value.returncode = 0
    success = adapter.render_video(
        project_path="dummy_workspace/my-video",
        comp_id="NewB2BReport",
        output_path="out.mp4",
    )
    assert success
    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    assert "npx" in args[0]
    assert "remotion" in args[0]
    assert "render" in args[0]
    assert "NewB2BReport" in args[0]
    assert "out.mp4" in args[0]
