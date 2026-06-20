import pytest

from tools.uupm_adapter import UUPMAdapter


@pytest.fixture
def adapter():
    return UUPMAdapter(workspace_path="/Users/rus/ai-tools")


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
