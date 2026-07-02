import os

from pypdf import PdfReader


def pdf_to_markdown(pdf_path, md_path):
    print(f"Extracting {pdf_path} -> {md_path}...")
    try:
        reader = PdfReader(pdf_path)
        text_content = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_content.append(f"\n## Page {i + 1}\n\n{text}\n")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Extracted Content: {os.path.basename(pdf_path)}\n\n")
            f.write("".join(text_content))
        print("Success!")
    except Exception as e:
        print(f"Error extracting {pdf_path}: {e}")


def main():
    downloads_dir = "/Users/rus/Downloads"
    output_dir = "/Users/rus/ai-tools/scratch/extracted_pdf"
    os.makedirs(output_dir, exist_ok=True)

    files = [
        "Отчет_по_GitHub-исследованию_для_lean_AI_agent-системы_(Agy).pdf",
        "От Aider до Karajan_ Дорожная карта внедрения 15 лучших open-source паттернов для создания безопасной и экономичной CLI-агентной системы.pdf",
        "Инженерное исследование GitHub-решений для улучшения lean AI-agent системы.pdf",
        "Исследование Lean AI_Agent Системы.pdf",
        "grok_report.pdf",
    ]

    for f in files:
        pdf_path = os.path.join(downloads_dir, f)
        # Уберем спецсимволы и пробелы из имени результирующего файла
        clean_name = (
            f.replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("___", "_")
            .replace(".pdf", ".md")
        )
        md_path = os.path.join(output_dir, clean_name)
        if os.path.exists(pdf_path):
            pdf_to_markdown(pdf_path, md_path)
        else:
            print(f"File not found: {pdf_path}")


if __name__ == "__main__":
    main()
