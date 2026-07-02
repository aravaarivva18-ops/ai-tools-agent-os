import re

from bs4 import BeautifulSoup


class SlopAuditor:
    def __init__(self):
        # Hues from 200 (cyan/blue) to 340 (magenta/pink) represent typical AI gradient ranges
        self.gradient_color_regex = re.compile(
            r'(purple|blue|pink|cyan|magenta|indigo|violet|oklch\([^)]*(2[0-9]{2}|3[0-3][0-9])[^)]*\))',
            re.IGNORECASE
        )
        self.metric_regex = re.compile(
            r'(\b\d+x\s+faster\b|\b\d+%\s+uptime\b|\btrusted\s+by\s+\d+[\d,]*\+?\s+teams\b|\b\+\d+%\s+conversion\b)',
            re.IGNORECASE
        )
        self.chrome_class_regex = re.compile(
            r'(browser-bar|traffic-light|window-control|mock-browser|mock-terminal|terminal-header)',
            re.IGNORECASE
        )
        self.transition_all_regex = re.compile(
            r'(transition\s*:\s*all|transition-all)',
            re.IGNORECASE
        )
        self.pure_neutral_regex = re.compile(
            r'(background(-color)?\s*:\s*(\s*#000(000)?\b|\s*#fff(fff)?\b|\s*black\b|\s*white\b))',
            re.IGNORECASE
        )
        self.geometric_anim_regex = re.compile(
            r'(@keyframes\s+\w+\s*\{[^}]*\b(width|height|margin|padding|top|left)\b[^}]*\}|transition\s*:\s*[^;]*(width|height|margin|padding|top|left))',
            re.IGNORECASE
        )

    def audit_content(self, *, html_content: str) -> dict:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract inline and embedded CSS
        style_blocks = [style.get_text() for style in soup.find_all('style')]
        inline_styles = [tag.get('style') for tag in soup.find_all(attrs={"style": True})]
        css_content = "\n".join(style_blocks + [style for style in inline_styles if style])

        critical = []
        major = []
        minor = []

        # Rule 1: Purple-gradient text or buttons
        if "background-clip" in css_content or "text-fill-color" in css_content:
            if self.gradient_color_regex.search(css_content):
                critical.append("gradient_headline: AI purple/blue gradient text styling detected.")

        # Rule 2: Fabricated metrics
        text_nodes = soup.find_all(string=True)
        all_text = " ".join([node.strip() for node in text_nodes if node.parent.name not in ['style', 'script']])
        metrics_found = self.metric_regex.findall(all_text)
        if metrics_found:
            critical.append(f"fabricated_metrics: Unverified metrics detected: {', '.join(set(metrics_found))}.")

        # Rule 3: Re-drawn OS chrome
        for tag in soup.find_all(class_=True):
            class_str = " ".join(tag.get('class', []))
            if self.chrome_class_regex.search(class_str):
                critical.append(f"redrawn_chrome: OS mock-up detected in class '{class_str}'.")

        # Rule 4: Transition-all
        if self.transition_all_regex.search(css_content):
            major.append("transition_all: Banned transition-all declaration detected.")

        # Rule 5: Centered Hero
        hero_tags = soup.find_all(class_=re.compile(r'hero', re.IGNORECASE))
        for hero in hero_tags:
            hero_style = css_content + (hero.get('style') or '')
            if "align-items: center" in hero_style or "text-align: center" in hero_style:
                # Hallmark bans fully centered vertical stacks for hero blocks
                major.append("centered_hero: Hero block is fully centered, causing template look.")
                break

        # Rule 6: Pure black/white background
        if self.pure_neutral_regex.search(css_content):
            major.append("pure_neutral: Absolute pure black or pure white background used.")

        # Rule 7: Emoji icons
        emoji_regex = re.compile(r'[✨🚀⚡🔥🎯✅]')
        for node in text_nodes:
            if node.parent.name not in ['style', 'script'] and emoji_regex.search(node):
                major.append(f"emoji_icons: Generative emoji icon '{node.strip()}' used as visual lead.")
                break

        # Rule 8: Geometric animation
        if self.geometric_anim_regex.search(css_content):
            major.append("geometric_animation: Animating layout geometry (width/height/margin/padding) is banned.")

        # Rule 9: Mobile clip / horizontal scroll safety
        if "overflow-x" not in css_content or not re.search(r'(html|body)[^}]*overflow-x\s*:\s*(clip|hidden)', css_content):
            major.append("no_mobile_clip: Missing overflow-x: clip/hidden constraint on html/body.")

        # Rule 10: Straight quotes and ellipses
        # Text analysis inside body only
        body_tag = soup.find('body')
        if body_tag:
            body_text_nodes = body_tag.find_all(string=True)
            body_text = " ".join([node.strip() for node in body_text_nodes if node.parent.name not in ['style', 'script']])
            if '"' in body_text or "'" in body_text:
                minor.append("straight_quotes: Straight quotes used instead of curly typographic quotes.")
            if "..." in body_text:
                minor.append("three_dots: Three periods used instead of unicode ellipsis.")

        # Compute verdict
        if critical:
            verdict = "ships as slop"
        elif len(major) >= 3:
            verdict = "reads as AI-generated"
        elif minor:
            verdict = "close, fix the minors"
        else:
            verdict = "impeccable"

        return {
            "critical": critical,
            "major": major,
            "minor": minor,
            "verdict": verdict
        }

if __name__ == '__main__':
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(description="Audit HTML and CSS files for AI-generated slop.")
    parser.add_argument("paths", nargs="+", help="Paths to files or directories to audit.")
    args = parser.parse_args()

    auditor = SlopAuditor()
    has_critical = False
    has_major_fail = False

    for path in args.paths:
        if not os.path.exists(path):
            print(f"\033[91mError: Path '{path}' does not exist.\033[0m")
            continue

        files_to_audit = []
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(('.html', '.htm', '.css')):
                        files_to_audit.append(os.path.join(root, file))
        else:
            files_to_audit.append(path)

        for file_path in files_to_audit:
            print(f"\nAuditing: {file_path}")
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"  \033[91mFailed to read file: {e}\033[0m")
                continue

            report = auditor.audit_content(html_content=content)

            # Output results
            if report["critical"]:
                print("  \033[91mCritical issues (slop tells):\033[0m")
                for issue in report["critical"]:
                    print(f"    - {issue}")
            if report["major"]:
                print("  \033[93mMajor issues (AI-style alerts):\033[0m")
                for issue in report["major"]:
                    print(f"    - {issue}")
            if report["minor"]:
                print("  \033[96mMinor issues (polishing needed):\033[0m")
                for issue in report["minor"]:
                    print(f"    - {issue}")

            # Verdict display
            color = "\033[92m" # Green
            if report["verdict"] == "ships as slop":
                color = "\033[91m" # Red
                has_critical = True
            elif report["verdict"] == "reads as AI-generated":
                color = "\033[93m" # Yellow
                has_major_fail = True
            elif report["verdict"] == "close, fix the minors":
                color = "\033[96m" # Cyan

            print(f"  Verdict: {color}{report['verdict'].upper()}\033[0m")

    # Exit code
    if has_critical:
        sys.exit(2)
    elif has_major_fail:
        sys.exit(1)
    else:
        sys.exit(0)

