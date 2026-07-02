from tools.slop_auditor import SlopAuditor


def test_clean_html_css():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Great Product</title>
        <style>
            body { background-color: oklch(98% 0.01 90); color: oklch(20% 0.01 90); font-family: "Instrument Serif", serif; overflow-x: clip; }
            .btn { transition: background-color 0.2s ease; outline: 2px solid transparent; }
            .btn:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 1px; }
            h1 { font-style: normal; line-height: 1.05; }
        </style>
    </head>
    <body>
        <header>
            <nav class="nav-minimal">
                <a href="/">Home</a>
                <a href="/about">About</a>
            </nav>
        </header>
        <main>
            <section class="hero-split">
                <h1>Crafted with intention</h1>
                <p>We build slow, high-quality tools for developers.</p>
                <button class="btn">Get started</button>
            </section>
        </main>
    </body>
    </html>
    """
    auditor = SlopAuditor()
    report = auditor.audit_content(html_content=html_content)
    assert report["verdict"] == "impeccable"
    assert len(report["critical"]) == 0
    assert len(report["major"]) == 0
    assert len(report["minor"]) == 0

def test_critical_slop():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            h1 {
                background: linear-gradient(to right, purple, blue);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .mock-browser { border: 1px solid #ccc; }
        </style>
    </head>
    <body>
        <h1>10x faster and 99.9% uptime guaranteed</h1>
        <div class="mock-browser">
            <div class="traffic-lights"></div>
        </div>
    </body>
    </html>
    """
    auditor = SlopAuditor()
    report = auditor.audit_content(html_content=html_content)
    assert report["verdict"] == "ships as slop"
    assert len(report["critical"]) > 0

def test_major_slop():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * { transition: all 0.3s ease; }
            body { background-color: #ffffff; }
            .hero { display: flex; flex-direction: column; align-items: center; text-align: center; min-height: 100vh; }
        </style>
    </head>
    <body>
        <section class="hero">
            <span>✨ Sparkle eyebrow</span>
            <h1>Centered Title</h1>
            <p>Centered paragraph text.</p>
            <button>🚀 Launch</button>
        </section>
    </body>
    </html>
    """
    auditor = SlopAuditor()
    report = auditor.audit_content(html_content=html_content)
    assert report["verdict"] == "reads as AI-generated"
    assert len(report["major"]) >= 3

def test_minor_slop():
    html_content = """
    <!DOCTYPE html>
    <html>
    <body>
        <p>This is "straight quotes" and it is bad...</p>
    </body>
    </html>
    """
    auditor = SlopAuditor()
    report = auditor.audit_content(html_content=html_content)
    assert report["verdict"] == "close, fix the minors"
    assert len(report["minor"]) > 0
