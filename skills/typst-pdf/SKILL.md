---
name: typst-pdf-generation
description: Guidelines for compiling vector-based PDF reports using the Typst engine.
---

# Typst PDF Report Generation

## 🛠️ Stack & Config
- **Engine**: `typst` (Python typst package)
- **Styling**: Typst markup language, system fonts (Arial/Helvetica/Liberation)

## 📐 Best Practices & Code Patterns

### 1. Typst Syntax Escaping (Avoiding Compile Failures)
- **Table Cells**: When passing dynamic string values from Python into Typst tables, **always** wrap them in double quotes `"value"` inside the array structure rather than passing them as raw code block containers `[value]`. This avoids compilation errors if the text contains Typst operators like `&` (column alignment), `$` (math mode), `_` (italics), or `*` (bold).
  - *Incorrect*: `table(columns: 2, [Title], [Description])`
  - *Correct*: `table(columns: 2, "Title", "Description")`
- **Dollar Signs**: Escape literal dollar signs as `\$` to prevent Typst from interpreting them as the boundary of a mathematical expression (which triggers unclosed delimiter errors).

### 2. Page Numbering (Typst 0.11+)
- **Always** wrap the page numbering logic inside a `#context` block to ensure dynamic evaluation of the page counters:
  ```typst
  #set page(
    footer: [
      #align(center)[
        #context counter(page).display("1 of 1", both: true)
      ]
    ]
  )
  ```

### 3. Dynamic Paths
- **Always** resolve template, asset, and font file paths dynamically relative to the executing Python script's location (using `pathlib.Path(__file__).parent`) rather than using hardcoded absolute or relative directory strings:
  ```python
  from pathlib import Path
  import typst

  template_dir = Path(__file__).parent / "templates"
  template_file = template_dir / "report.typ"
  
  # Read template and compile
  with open(template_file, "r") as f:
      template_content = f.read()
  ```

## ⚠️ Common Pitfalls & Anti-patterns
- **Prohibited**: Do not import or use `reportlab` or any related canvas/platypus packages.
- **Error**: Modifying a Typst template string with simple `.format()` or f-strings containing unescaped brace brackets `{}` (will crash the python compiler). Use dedicated placeholder variables (like `__TITLE__`) and `.replace("__TITLE__", val)` for string interpolation.
- **Error**: Setting fixed page heights or static footer page numbers that fail to scale dynamically for multi-page reports.

## 🔄 Verification Checklist
1. All report exports use the `typst` python compilation library.
2. Dynamic table strings are formatted as double-quoted strings `"..."` inside the Typst source.
3. Page numbers are configured using the `#context` wrapper.
4. Run `make check` to verify Python script paths resolve cleanly.
