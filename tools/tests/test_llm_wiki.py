from llm_wiki import LLMWiki


def test_wiki_init_creates_directories(tmp_path):
    """Test that LLMWiki initializes directories relative to the root directory."""
    LLMWiki(root_dir=tmp_path)
    assert (tmp_path / "RAW").is_dir()
    assert (tmp_path / "wiki").is_dir()
    assert (tmp_path / "wiki" / "index.md").is_file()
    assert (tmp_path / "wiki" / "Log.md").is_file()


def test_extract_links():
    """Test standard extraction of Obsidian-style [[Wiki Links]]."""
    text = (
        "Here is a [[Wiki Note]] and another [[Second Note|Alternative Name]] in text."
    )
    links = LLMWiki.extract_wiki_links(text)
    assert links == ["Wiki Note", "Second Note"]


def test_injest_workflow(tmp_path):
    """Test the injest workflow from RAW to wiki."""
    wiki = LLMWiki(root_dir=tmp_path)

    # Put a raw file in RAW
    raw_file = tmp_path / "RAW" / "project_intro.md"
    raw_file.write_text(
        "Context about [[Feature A]] and [[Feature B]]. Project overview."
    )

    wiki.injest()

    # Check that note files are created
    feature_a_file = tmp_path / "wiki" / "Feature A.md"
    feature_b_file = tmp_path / "wiki" / "Feature B.md"
    project_intro_file = tmp_path / "wiki" / "project_intro.md"

    assert project_intro_file.is_file()
    assert "Context about [[Feature A]]" in project_intro_file.read_text()

    # Automatically created note stubs should exist
    assert feature_a_file.is_file()
    assert feature_b_file.is_file()
    assert "stub" in feature_a_file.read_text().lower()

    # Log and index should be updated
    log_content = (tmp_path / "wiki" / "Log.md").read_text()
    index_content = (tmp_path / "wiki" / "index.md").read_text()

    assert "project_intro" in log_content
    assert "[[project_intro]]" in index_content


def test_query_recursive_context(tmp_path):
    """Test query fetches recursive context starting from a node."""
    wiki = LLMWiki(root_dir=tmp_path)

    # Create notes manually
    (tmp_path / "wiki" / "index.md").write_text("Index linking to [[PageA]]")
    (tmp_path / "wiki" / "PageA.md").write_text("This is PageA linking to [[PageB]].")
    (tmp_path / "wiki" / "PageB.md").write_text("This is PageB, leaf node.")

    context = wiki.query("PageA", max_depth=2)
    assert "PageA" in context
    assert "PageB" in context
    assert "This is PageA" in context
    assert "This is PageB" in context


def test_lint_detects_broken_links_and_duplicates(tmp_path):
    """Test that linting detects broken links and identifies actions needed."""
    wiki = LLMWiki(root_dir=tmp_path)

    # Create a note with a broken link (no stub or file exists for PageC)
    (tmp_path / "wiki" / "PageA.md").write_text(
        "Links to [[PageC]] which doesn't exist."
    )

    report = wiki.lint()
    assert len(report["broken_links"]) == 1
    assert report["broken_links"][0] == ("PageA", "PageC")
