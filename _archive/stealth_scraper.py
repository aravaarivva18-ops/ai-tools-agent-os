import json
import os

from curl_cffi import requests

try:
    from tools.config import get_workspace_root
except ImportError:
    from config import get_workspace_root

url = "https://playerok.com/_next/data/xvH1l2wF3QS26nQSbvK9I/products/6227c2a24866-avtovydacha-bez-slyota-na-vash-akkaunt-gemini-ai-pro-18-months.json"

print("Requesting JSON url:", url)

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://playerok.com/products/6227c2a24866-avtovydacha-bez-slyota-na-vash-akkaunt-gemini-ai-pro-18-months",
}

try:
    response = session.get(url, impersonate="chrome110", headers=headers, timeout=15)
    print("Status code:", response.status_code)
    print("Response headers:", dict(response.headers))

    json_data = response.json()
    print("Successfully parsed JSON response!")

    output_path = os.path.join(
        get_workspace_root(), "vault", "playerok_api_response.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"Saved to {output_path}")

except Exception as e:
    print("Request failed:", e)
    if "response" in locals() and response.text:
        print("Response text snippet:", repr(response.text[:500]))
