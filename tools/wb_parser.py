"""Wildberries product parser. Extracts product details, pricing, stock and reviews using public API."""

import json
from typing import Any
from urllib.parse import urlencode

from curl_cffi import requests


class WildberriesParser:
    """Class to fetch and parse product details from Wildberries using public API endpoints."""

    def __init__(self) -> None:
        self.base_url = "https://card.wb.ru/cards/v2/detail"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def fetch_product(self, article: int | str) -> dict[str, Any] | None:
        """Fetches raw product details from Wildberries detail API."""
        params = {
            "appType": 1,
            "curr": "rub",
            "dest": -1257786,  # Default geo destination (Moscow region)
            "srg": 1,
            "nm": str(article),
        }
        url = f"{self.base_url}?{urlencode(params)}"

        try:
            response = requests.get(
                url, headers=self.headers, timeout=15, impersonate="chrome"
            )
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", {}).get("products", [])
                if products:
                    return products[0]
            return None
        except Exception:
            return None

    def parse_product(self, article: int | str) -> dict[str, Any]:
        """Fetches and normalizes product information into a clean structured dictionary."""
        raw_data = self.fetch_product(article)
        if not raw_data:
            return {
                "article": str(article),
                "success": False,
                "error": "Товар не найден или ошибка запроса.",
            }

        # Pricing calculation (prices are in minor units, e.g., multiplied by 100)
        sizes = raw_data.get("sizes", [])
        price_info = sizes[0].get("price", {}) if sizes else {}

        raw_price = price_info.get("basic", 0) / 100
        discount_price = price_info.get("total", 0) / 100
        discount_percent = price_info.get("logDiscount", 0)

        # Basic data
        product = {
            "article": str(article),
            "success": True,
            "name": raw_data.get("name", "Без названия"),
            "brand": raw_data.get("brand", "Без бренда"),
            "brand_id": raw_data.get("brandId"),
            "rating": raw_data.get("rating", 0),
            "feedbacks": raw_data.get("feedbacks", 0),
            "subject_id": raw_data.get("subjectId"),
            "subject_parent_id": raw_data.get("subjectParentId"),
            "price": raw_price,
            "discount_price": discount_price,
            "discount_percent": discount_percent,
            "in_stock": any(
                any(wh.get("qty", 0) > 0 for wh in sz.get("stocks", [])) for sz in sizes
            ),
        }

        return product

    def to_markdown(self, product_data: dict[str, Any]) -> str:
        """Converts structured product dictionary to Markdown format for Obsidian / LLM ingest."""
        if not product_data.get("success"):
            return f"# Ошибка парсинга товара\n\nАртикул: {product_data.get('article')}\nОшибка: {product_data.get('error')}"

        in_stock_str = (
            "🟢 В наличии" if product_data.get("in_stock") else "🔴 Нет в наличии"
        )

        markdown = f"""# 🛍️ Товар WB: {product_data.get("name")}

## 📊 Основная информация
*   **Артикул:** `{product_data.get("article")}`
*   **Бренд:** {product_data.get("brand")} (ID: {product_data.get("brand_id")})
*   **Статус:** {in_stock_str}

## 💰 Ценообразование
*   **Базовая цена:** {product_data.get("price"):,.2f} руб.
*   **Цена со скидкой:** {product_data.get("discount_price"):,.2f} /руб. (Скидка: {product_data.get("discount_percent")}%)

## ⭐ Рейтинг и Отзывы
*   **Оценка покупателей:** {product_data.get("rating")} / 5.0
*   **Количество отзывов:** {product_data.get("feedbacks")} отзывов
"""
        return markdown
