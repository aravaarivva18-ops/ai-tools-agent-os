import csv
import os
import subprocess  # nosec B404

try:
    from tools.config import get_workspace_root
except ImportError:
    from config import get_workspace_root

try:
    from tools.interaction_core import InteractionCore
except ImportError:
    try:
        from interaction_core import InteractionCore
    except ImportError:
        InteractionCore = None


class UUPMAdapter:
    """
    Adapter for UI/UX Pro Max design intelligence system.
    Interfaces with uipro-cli assets installed under .agent/skills/ui-ux-pro-max/data/
    """

    def __init__(self, workspace_path: str | None = None):
        if workspace_path is None:
            workspace_path = str(get_workspace_root())
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

    def _get_google_font_url(self, font_name: str) -> str:
        """Helper to construct Google Fonts URL for a given font name."""
        system_fonts = {
            "arial",
            "helvetica",
            "georgia",
            "times new roman",
            "times",
            "courier new",
            "courier",
            "verdana",
            "tahoma",
            "trebuchet ms",
            "impact",
            "comic sans ms",
            "sans-serif",
            "serif",
            "monospace",
        }
        if not font_name or font_name.lower() in system_fonts:
            return ""
        encoded_name = font_name.replace(" ", "+")
        return f"https://fonts.googleapis.com/css2?family={encoded_name}:wght@400;500;700&display=swap"

    def generate_design_md_content(
        self, product_type: str, typography_name: str
    ) -> str:
        """Generates YAML frontmatter content for DESIGN.md based on database rules."""
        palette = self.get_color_palette(product_type)
        typo = self.get_typography_pairing(typography_name)

        primary = palette.get("Primary (Hex)", "#1a365d") if palette else "#1a365d"
        secondary = palette.get("Secondary (Hex)", "#2c5282") if palette else "#2c5282"
        cta = palette.get("CTA (Hex)", "#f97316") if palette else "#f97316"
        background = (
            palette.get("Background (Hex)", "#f7fafc") if palette else "#f7fafc"
        )
        text_val = palette.get("Text (Hex)", "#2d3748") if palette else "#2d3748"
        border = palette.get("Border (Hex)", "#e2e8f0") if palette else "#e2e8f0"

        heading_font = typo.get("Heading Font", "Inter") if typo else "Inter"
        body_font = typo.get("Body Font", "Inter") if typo else "Inter"

        # Check for fallback fonts if typography values are generic sans-serif
        heading_font_family = (
            f'"{heading_font}, sans-serif"'
            if heading_font.lower() != "sans-serif"
            else '"sans-serif"'
        )
        body_font_family = (
            f'"{body_font}, sans-serif"'
            if body_font.lower() != "sans-serif"
            else '"sans-serif"'
        )

        return f"""---
name: {product_type.replace(" ", "")}Theme
colors:
  primary: "{primary}"
  secondary: "{secondary}"
  cta: "{cta}"
  neutral: "{background}"
  text: "{text_val}"
  border: "{border}"
typography:
  h1:
    fontFamily: {heading_font_family}
    fontSize: 2.25rem
    fontWeight: 700
  body:
    fontFamily: {body_font_family}
    fontSize: 1rem
rounded:
  md: 8px
spacing:
  md: 16px
components:
  button-primary:
    backgroundColor: "{primary}"
    textColor: "{background}"
    rounded: "{{rounded.md}}"
    padding: 12px 24px
---

## Overview
Дизайн-система сгенерирована автоматически на основе UI/UX Pro Max правил для категории "{product_type}".
"""

    def generate_css_variables(self, product_type: str, typography_name: str) -> str:
        """Generates CSS file content with Google Fonts imports and theme variables."""
        palette = self.get_color_palette(product_type)
        typo = self.get_typography_pairing(typography_name)

        primary = palette.get("Primary (Hex)", "#1a365d") if palette else "#1a365d"
        secondary = palette.get("Secondary (Hex)", "#2c5282") if palette else "#2c5282"
        cta = palette.get("CTA (Hex)", "#f97316") if palette else "#f97316"
        background = (
            palette.get("Background (Hex)", "#f7fafc") if palette else "#f7fafc"
        )
        text_val = palette.get("Text (Hex)", "#2d3748") if palette else "#2d3748"
        border = palette.get("Border (Hex)", "#e2e8f0") if palette else "#e2e8f0"

        heading_font = typo.get("Heading Font", "Inter") if typo else "Inter"
        body_font = typo.get("Body Font", "Inter") if typo else "Inter"

        imports = []
        h_url = self._get_google_font_url(heading_font)
        if h_url:
            imports.append(f'@import url("{h_url}");')
        b_url = self._get_google_font_url(body_font)
        if b_url and b_url != h_url:
            imports.append(f'@import url("{b_url}");')

        import_block = "\n".join(imports)

        # Generate spring variables from InteractionCore
        spring_vars = ""
        spring_styles = ""
        if InteractionCore:
            try:
                pop_cfg = InteractionCore.generate_ui_config("pop", "button")
                smooth_cfg = InteractionCore.generate_ui_config("smooth", "button")
                snappy_cfg = InteractionCore.generate_ui_config("snappy", "button")

                spring_vars = f"""
  /* Tactile Springs (Emil Kowalski presets) */
  --spring-pop-duration: {pop_cfg["css_variables"].get("--spring-duration", "0.35s")};
  --spring-pop-timing-curve: {pop_cfg["css_variables"]["--spring-timing-curve"]};
  --spring-pop-blur: {pop_cfg["css_variables"]["--motion-blur"]};
  --spring-pop-scale: {pop_cfg["css_variables"]["--scale-active"]};

  --spring-smooth-duration: {smooth_cfg["css_variables"].get("--spring-duration", "0.35s")};
  --spring-smooth-timing-curve: {smooth_cfg["css_variables"]["--spring-timing-curve"]};
  --spring-smooth-blur: {smooth_cfg["css_variables"]["--motion-blur"]};

  --spring-snappy-duration: {snappy_cfg["css_variables"].get("--spring-duration", "0.35s")};
  --spring-snappy-timing-curve: {snappy_cfg["css_variables"]["--spring-timing-curve"]};
  --spring-snappy-blur: {snappy_cfg["css_variables"]["--motion-blur"]};
  --spring-snappy-scale: {snappy_cfg["css_variables"]["--scale-active"]};
"""
                spring_styles = """
/* Interactive components tactile springs */
button, .btn, [role="button"], input[type="submit"] {
  transition: transform var(--spring-snappy-duration) var(--spring-snappy-timing-curve),
              filter var(--spring-snappy-duration) var(--spring-snappy-timing-curve);
  will-change: transform;
}

button:active, .btn:active, [role="button"]:active, input[type="submit"]:active {
  transform: scale(var(--spring-snappy-scale));
  filter: var(--spring-snappy-blur);
}
"""
            except Exception:
                pass

        return f"""{import_block}

/* UI/UX Pro Max Generated theme for {product_type} */
@theme {{
  --color-primary: {primary};
  --color-secondary: {secondary};
  --color-cta: {cta};
  --color-background: {background};
  --color-text: {text_val};
  --color-border: {border};

  --font-heading: "{heading_font}", sans-serif;
  --font-body: "{body_font}", sans-serif;
{spring_vars}}}
{spring_styles}"""

    def write_design_assets(
        self,
        product_type: str,
        typography_name: str,
        output_dir: str = ".",
        generate_css: bool = True,
    ) -> dict[str, str]:
        """Generates and writes design assets to the specified output directory."""
        os.makedirs(output_dir, exist_ok=True)

        design_md_path = os.path.join(output_dir, "DESIGN.md")
        design_md_content = self.generate_design_md_content(
            product_type, typography_name
        )
        with open(design_md_path, "w", encoding="utf-8") as f:
            f.write(design_md_content)

        results = {"design_md": os.path.abspath(design_md_path)}

        if generate_css:
            css_path = os.path.join(output_dir, "theme.css")
            css_content = self.generate_css_variables(product_type, typography_name)
            with open(css_path, "w", encoding="utf-8") as f:
                f.write(css_content)
            results["theme_css"] = os.path.abspath(css_path)

        return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="UI/UX Pro Max CLI design system generator"
    )
    parser.add_argument(
        "--product", required=True, help="Product type (e.g. SaaS, e-commerce)"
    )
    parser.add_argument(
        "--typo", required=True, help="Typography pairing name or category"
    )
    parser.add_argument(
        "--out-dir", default=".", help="Output directory for generated assets"
    )
    parser.add_argument("--css", action="store_true", help="Generate theme.css file")
    args = parser.parse_args()

    # Get absolute workspace path dynamically
    current_file_path = os.path.abspath(__file__)
    workspace_dir = os.path.dirname(os.path.dirname(current_file_path))

    adapter = UUPMAdapter(workspace_path=workspace_dir)
    try:
        paths = adapter.write_design_assets(
            args.product, args.typo, args.out_dir, generate_css=args.css
        )
        print("success: Generated design assets:")
        print(f"  - DESIGN.md: {paths['design_md']}")
        if args.css:
            print(f"  - theme.css: {paths['theme_css']}")
    except Exception as e:
        print(f"error: {e}")
        import sys

        sys.exit(1)
