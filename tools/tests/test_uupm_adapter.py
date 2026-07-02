import os

import pytest

from tools.uupm_adapter import UUPMAdapter


@pytest.fixture
def adapter():
    return UUPMAdapter()


def test_init_environment(adapter):
    # Tests execution of init offline command
    success = adapter.init_environment(force=True)
    assert success is True


def test_load_csv_data(adapter):
    colors = adapter.load_csv_data("colors.csv")
    assert len(colors) > 0
    assert "Product Type" in colors[0]


def test_get_color_palette(adapter):
    saas_palette = adapter.get_color_palette("SaaS")
    assert saas_palette is not None
    assert saas_palette["Primary (Hex)"] == "#2563EB"

    none_palette = adapter.get_color_palette("NonExistentProductType")
    assert none_palette is None


def test_get_typography_pairing(adapter):
    typo = adapter.get_typography_pairing("Tech Startup")
    assert typo is not None
    assert typo["Heading Font"] == "Space Grotesk"
    assert typo["Body Font"] == "DM Sans"


def test_get_ux_guidelines(adapter):
    matches = adapter.get_ux_guidelines("forms")
    assert isinstance(matches, list)


def test_generate_typst_design_block(adapter):
    typst_code = adapter.generate_typst_design_block("SaaS", "Tech Startup")
    assert 'primary-color = rgb("#2563EB")' in typst_code
    assert 'heading-font = "Space Grotesk"' in typst_code
    assert 'body-font = "DM Sans"' in typst_code


def test_generate_design_md_content(adapter):
    content = adapter.generate_design_md_content("SaaS", "Tech Startup")
    assert "name: SaaSTheme" in content
    assert 'primary: "#2563EB"' in content
    assert 'fontFamily: "Space Grotesk, sans-serif"' in content
    assert 'fontFamily: "DM Sans, sans-serif"' in content


def test_generate_css_variables(adapter):
    content = adapter.generate_css_variables("SaaS", "Tech Startup")
    assert (
        '@import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap");'
        in content
    )
    assert (
        '@import url("https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap");'
        in content
    )
    assert "--color-primary: #2563EB;" in content
    assert '--font-heading: "Space Grotesk", sans-serif;' in content


def test_write_design_assets(adapter, tmp_path):
    output_dir = str(tmp_path)
    paths = adapter.write_design_assets(
        "SaaS", "Tech Startup", output_dir=output_dir, generate_css=True
    )

    assert "design_md" in paths
    assert "theme_css" in paths

    assert os.path.exists(paths["design_md"])
    assert os.path.exists(paths["theme_css"])

    with open(paths["design_md"], encoding="utf-8") as f:
        md_content = f.read()
        assert "name: SaaSTheme" in md_content

    with open(paths["theme_css"], encoding="utf-8") as f:
        css_content = f.read()
        assert "@theme" in css_content
