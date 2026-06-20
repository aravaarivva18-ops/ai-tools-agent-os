import csv
import os
import subprocess  # nosec B404


class UUPMAdapter:
    """
    Adapter for UI/UX Pro Max design intelligence system.
    Interfaces with uipro-cli assets installed under .agent/skills/ui-ux-pro-max/data/
    """

    def __init__(self, workspace_path: str = "/Users/rus/ai-tools"):
        self.workspace_path = workspace_path
        self.skills_path = os.path.join(
            workspace_path, "tools", ".agent", "skills", "ui-ux-pro-max"
        )
        self.data_path = os.path.join(self.skills_path, "data")

    def init_environment(self, force: bool = False) -> bool:
        """Initializes the uipro-cli system for the project workspace."""
        cmd = ["npx", "uipro-cli", "init", "-a", "antigravity", "--offline"]
        if force:
            cmd.append("--force")

        try:
            result = subprocess.run(  # nosec B603
                cmd,
                cwd=os.path.join(self.workspace_path, "tools"),
                capture_output=True,
                text=True,
                check=True,
            )
            return (
                "success" in result.stdout.lower()
                or "installed successfully" in result.stdout.lower()
            )
        except subprocess.SubprocessError:
            return False

    def load_csv_data(self, filename: str) -> list[dict[str, str]]:
        """Loads design analytical data from local CSV database."""
        file_path = os.path.join(self.data_path, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"UUPM CSV database file not found at: {file_path}")

        data = []
        with open(file_path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
        return data

    def get_color_palette(self, product_type: str) -> dict[str, str] | None:
        """Retrieves colors (primary, secondary, CTA, backgrounds) for product category."""
        palettes = self.load_csv_data("colors.csv")
        for p in palettes:
            if product_type.lower() in p.get("Product Type", "").lower():
                return p
        return None

    def get_typography_pairing(self, category_or_name: str) -> dict[str, str] | None:
        """Retrieves typography pairings for fonts and headings."""
        pairings = self.load_csv_data("typography.csv")
        for tp in pairings:
            if (
                category_or_name.lower() in tp.get("Font Pairing Name", "").lower()
                or category_or_name.lower() in tp.get("Category", "").lower()
            ):
                return tp
        return None

    def get_ux_guidelines(self, keyword: str) -> list[dict[str, str]]:
        """Retrieves matching UX guidelines for a specific keyword."""
        guidelines = self.load_csv_data("ux-guidelines.csv")
        matches = []
        for g in guidelines:
            text_to_search = " ".join(g.values()).lower()
            if keyword.lower() in text_to_search:
                matches.append(g)
        return matches

    def generate_typst_design_block(
        self, product_type: str, typography_name: str
    ) -> str:
        """Generates Typst design block variables code for integration with Typst reports."""
        palette = self.get_color_palette(product_type)
        typo = self.get_typography_pairing(typography_name)

        primary = palette.get("Primary (Hex)", "#000000") if palette else "#1a365d"
        secondary = palette.get("Secondary (Hex)", "#000000") if palette else "#2c5282"
        cta = palette.get("CTA (Hex)", "#000000") if palette else "#f97316"
        background = (
            palette.get("Background (Hex)", "#ffffff") if palette else "#f7fafc"
        )
        text_val = palette.get("Text (Hex)", "#000000") if palette else "#2d3748"
        border = palette.get("Border (Hex)", "#e2e8f0") if palette else "#e2e8f0"

        heading_font = typo.get("Heading Font", "Arial") if typo else "Arial"
        body_font = typo.get("Body Font", "Arial") if typo else "Arial"

        typst_code = f"""// UI/UX Pro Max generated design variables for {product_type}
#let primary-color = rgb("{primary}")
#let secondary-color = rgb("{secondary}")
#let cta-color = rgb("{cta}")
#let bg-color = rgb("{background}")
#let text-color = rgb("{text_val}")
#let border-color = rgb("{border}")

#let heading-font = "{heading_font}"
#let body-font = "{body_font}"
"""
        return typst_code
