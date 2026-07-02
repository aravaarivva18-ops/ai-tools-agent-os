import os
import shutil
import tempfile

import pytest
from tools.aeo_generator import AEOGenerator


@pytest.fixture
def temp_project_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_aeo_generation(temp_project_dir):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Demo SaaS Platform</title>
        <meta name="description" content="A next-generation platform for managing AI workflows.">
    </head>
    <body>
        <h1>Welcome to AI Flow</h1>
        <h2>Core features</h2>
        <h3>Data ingestion</h3>
        <form action="/subscribe" method="post">
            <input type="email" name="user_email" placeholder="Enter email">
            <button type="submit">Subscribe</button>
        </form>
    </body>
    </html>
    """

    # Setup test file structure
    index_path = os.path.join(temp_project_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    generator = AEOGenerator()
    generator.generate_aeo(project_dir=temp_project_dir)

    # Check llms.txt creation
    llms_path = os.path.join(temp_project_dir, "llms.txt")
    assert os.path.exists(llms_path)
    with open(llms_path, encoding="utf-8") as f:
        llms_content = f.read()

    assert "Demo SaaS Platform" in llms_content
    assert "A next-generation platform for managing AI workflows" in llms_content
    assert "Welcome to AI Flow" in llms_content
    assert "Core features" in llms_content
    assert "Form (user_email)" in llms_content

    # Check robots.txt creation and updates
    robots_path = os.path.join(temp_project_dir, "robots.txt")
    assert os.path.exists(robots_path)
    with open(robots_path, encoding="utf-8") as f:
        robots_content = f.read()

    assert "User-agent: GPTBot" in robots_content
    assert "Allow: /llms.txt" in robots_content

    # Check JSON-LD insertion in modified HTML
    with open(index_path, encoding="utf-8") as f:
        modified_html = f.read()

    assert "application/ld+json" in modified_html
    assert "https://schema.org" in modified_html
    assert "WebSite" in modified_html
    assert "Demo SaaS Platform" in modified_html
