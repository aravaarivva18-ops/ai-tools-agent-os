#!/usr/bin/env python3
"""Tests to verify that project constitutions and guides are updated to v10 with latest integrations."""

from pathlib import Path


def test_constitutions_contain_latest_integrations():
    workspace_root = Path(__file__).resolve().parents[2]
    home_dir = workspace_root.parent  # /Users/rus/
    
    files_to_check = [
        home_dir / "GEMINI_ANTIGRAVITY.md",
        home_dir / "STUDENT_GUIDE.md",
        workspace_root / "CLAUDE.md",
        workspace_root / "AGENTS.md",
        workspace_root / "attachments" / "gemini_bot_knowledge_base.md",
    ]
    
    for f_path in files_to_check:
        assert f_path.exists(), f"File {f_path} does not exist"
        content = f_path.read_text(encoding="utf-8").lower()
        
        # Check v10 Solo Loop references
        assert "v10" in content, f"v10 Solo Loop reference missing in {f_path.name}"
        
        # Verify that either levelsio, karpathy vibe coding, or buyback metrics are mentioned
        has_new_philosophies = any(
            kw in content
            for kw in ["levelsio", "karpathy", "buyback", "pre-delegation", "is_ui", "is_seo", "is_scale", "is_mcp"]
        )
        assert has_new_philosophies, f"New integrations (vibe coding, buyback, JIT templates) missing in {f_path.name}"
