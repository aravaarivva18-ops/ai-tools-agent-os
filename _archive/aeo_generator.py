import argparse
import json
import os
import re

from bs4 import BeautifulSoup


class AEOGenerator:
    def __init__(self):
        self.ai_agents = [
            "GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended",
            "Applebot-Extended", "Anthropic-AI", "Cohere-AI"
        ]

    def generate_aeo(self, *, project_dir: str) -> None:
        if not os.path.exists(project_dir):
            print(f"Error: Directory '{project_dir}' does not exist.")
            return

        html_files = []
        for root, _, files in os.walk(project_dir):
            for file in files:
                if file.endswith(('.html', '.htm')):
                    # Skip common build/dependency folders
                    if not any(x in root for x in ['node_modules', 'dist', '.next', 'out']):
                        html_files.append(os.path.join(root, file))

        if not html_files:
            return

        # Core logic: parse HTML and synthesize llms.txt structure
        pages_summary = []
        for file_path in html_files:
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"Failed to read {file_path}: {e}")
                continue

            soup = BeautifulSoup(content, 'html.parser')

            title = soup.title.string.strip() if (soup.title and soup.title.string) else "Untitled Page"
            meta_desc = ""
            desc_tag = soup.find('meta', attrs={"name": "description"})
            if desc_tag:
                meta_desc = desc_tag.get('content', '').strip()

            rel_path = os.path.relpath(file_path, project_dir)
            headings = [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3']) if h.get_text()]
            forms = []
            for form in soup.find_all('form'):
                inputs = [inp.get('name') or inp.get('type') for inp in form.find_all(['input', 'textarea', 'select']) if inp.get('type') != 'hidden']
                forms.append(f"Form ({', '.join(filter(None, inputs))})")

            # Автогенерация Schema.org JSON-LD для SEO/AEO
            schema_type = "WebSite" if rel_path in ("index.html", "index.htm") else "WebPage"
            schema_data = {
                "@context": "https://schema.org",
                "@type": schema_type,
                "name": title,
                "description": meta_desc,
                "url": f"./{rel_path}"
            }
            if schema_type == "WebSite":
                schema_data["publisher"] = {
                    "@type": "Organization",
                    "name": "System"
                }

            # Удаляем старый автогенерированный JSON-LD для предотвращения дублирования
            for old_ld in soup.find_all('script', type='application/ld+json'):
                if old_ld.string and "https://schema.org" in old_ld.string:
                    old_ld.decompose()

            # Инжектируем новый JSON-LD
            ld_tag = soup.new_tag('script', type='application/ld+json')
            ld_tag.string = json.dumps(schema_data, indent=2, ensure_ascii=False)

            if soup.head:
                soup.head.append(ld_tag)
            elif soup.body:
                soup.body.insert(0, ld_tag)
            else:
                soup.append(ld_tag)

            # Сохраняем обновленный HTML файл
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
            except Exception as e:
                print(f"Failed to save modified HTML {file_path}: {e}")

            pages_summary.append({
                "path": rel_path,
                "title": title,
                "description": meta_desc,
                "headings": headings[:10],
                "forms": forms
            })

        # Emitting llms.txt content
        llms_lines = [
            "# AI Agent Readme (llms.txt)",
            f"\nThis project is a web application located at: {os.path.basename(os.path.abspath(project_dir))}\n",
            "## Structure & Navigation Map\n"
        ]

        for page in pages_summary:
            llms_lines.append(f"### Page: `{page['path']}`")
            llms_lines.append(f"* **Title:** {page['title']}")
            if page['description']:
                llms_lines.append(f"* **Description:** {page['description']}")
            if page['headings']:
                llms_lines.append("* **Key Sections:**")
                for heading in page['headings']:
                    cleaned_heading = re.sub(r'\s+', ' ', heading)
                    llms_lines.append(f"  * {cleaned_heading}")
            if page['forms']:
                llms_lines.append("* **Interactive Actions:**")
                for form in page['forms']:
                    llms_lines.append(f"  * {form}")
            llms_lines.append("")

        llms_path = os.path.join(project_dir, "llms.txt")
        with open(llms_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(llms_lines))
        print(f"✅ Created llms.txt at: {llms_path}")

        # Update robots.txt to guide AI agents to llms.txt
        robots_path = os.path.join(project_dir, "robots.txt")
        robots_content = ""
        if os.path.exists(robots_path):
            try:
                with open(robots_path, encoding='utf-8') as f:
                    robots_content = f.read()
            except Exception as e:
                print(f"Failed to read existing robots.txt: {e}")

        # Append agent rules if they aren't already present
        new_rules = []
        for agent in self.ai_agents:
            if f"User-agent: {agent}" not in robots_content:
                new_rules.append(f"User-agent: {agent}\nAllow: /\nAllow: /llms.txt")

        if new_rules:
            separator = "\n\n" if robots_content else ""
            robots_content += separator + "\n\n".join(new_rules) + "\n"
            with open(robots_path, 'w', encoding='utf-8') as f:
                f.write(robots_content)
            print(f"✅ Updated robots.txt with AI agent rules at: {robots_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate AI-friendly llms.txt and robots.txt.")
    parser.add_argument("dir", help="Directory of the web project to optimize.")
    args = parser.parse_args()

    generator = AEOGenerator()
    generator.generate_aeo(project_dir=args.dir)
